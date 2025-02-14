import pandas as pd
import os
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime, timedelta

class TranscriptStorageHandler:
    def __init__(self, bucket_name, service_account_path):
        """Initialize the storage client and bucket."""
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # Initialize storage client with the service account credentials
        self.storage_client = storage.Client(credentials=credentials)
        self.bucket = self.storage_client.bucket(bucket_name)
        
        # Store credentials for signing URLs
        self.credentials = credentials


    def upload_transcript(self, file_path, company, year, quarter):
        """
        Upload a transcript file to GCP Storage.
        
        Args:
            file_path (str): Local path to the transcript file
            company (str): Company name
            year (str): Year of the transcript
            quarter (str): Quarter (1, 2, 3, 4)
            
        Returns:
            str: The GCP Storage path of the uploaded file
        """
        # Create a standardized blob path - store directly in the quarter folder
        blob_path = f"metadata/transcripts/{company}/{year}/{quarter}/{os.path.basename(file_path)}"
        blob = self.bucket.blob(blob_path)
        
        # Upload the file
        blob.upload_from_filename(file_path)
        
        return blob_path

    def get_transcript_url(self, company, year, quarter):
        """
        Generate a signed URL for accessing the transcript.
        Since we know there's only one file per (company, year, quarter),
        we just get the first file in the path.
        
        Args:
            company (str): Company name
            year (str): Year of the transcript
            quarter (str): Quarter (1, 2, 3, 4)
            
        Returns:
            str: Signed URL for accessing the transcript, or None if no file found
        """
        try:
            # Construct the prefix path
            prefix = f"metadata/transcripts/{company}/{year}/{quarter}/"
            
            # List blobs with the prefix (should only be one)
            blobs = list(self.bucket.list_blobs(prefix=prefix, max_results=1))
            
            if not blobs:
                print(f"No transcript found for {company} {year} {quarter}")
                return None
                
            # Get the first (and only) blob
            blob = blobs[0]
            
            # Generate a signed URL that expires in 1 hour
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(hours=1),
                service_account_email=self.credentials.service_account_email,
                access_token=None,
                credentials=self.credentials
            )
            
            return url
        except Exception as e:
            print(f"Error generating signed URL: {str(e)}")
            raise

def upload_transcripts_from_csv(csv_path, transcripts_folder, bucket_name):
    """
    Upload transcripts to GCP Storage based on CSV metadata.
    
    Args:
        csv_path (str): Path to the CSV file containing transcript metadata
        transcripts_folder (str): Path to the folder containing transcript files
        bucket_name (str): Name of the GCP bucket
    """
    # Initialize our storage handler
    handler = TranscriptStorageHandler(bucket_name)
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Track successful and failed uploads
    successful = 0
    failed = 0
    failed_files = []
    
    # Process each row in the CSV
    for index, row in df.iterrows():
        try:
            company = row['Company Name']
            year = str(row['CALENDAR_YEAR'])
            quarter = str(row['CALENDAR_QTR'])
            filename = f"{row['Transcript_Filename']}.txt"
            
            # Construct the full path to the transcript file
            transcript_path = os.path.join(transcripts_folder, filename)
            
            # Check if file exists
            if not os.path.exists(transcript_path):
                print(f"File not found: {transcript_path}")
                failed += 1
                failed_files.append(filename)
                continue
            
            # Upload the file
            blob_path = handler.upload_transcript(
                file_path=transcript_path,
                company=company,
                year=year,
                quarter=quarter
            )
            
            print(f"Successfully uploaded: {blob_path}")
            successful += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            failed += 1
            failed_files.append(filename)
    
    # Print summary
    print("\nUpload Summary:")
    print(f"Successfully uploaded: {successful} files")
    print(f"Failed to upload: {failed} files")
    
    if failed_files:
        print("\nFailed files:")
        for file in failed_files:
            print(f"- {file}")

def main():
    # Configuration
    CSV_PATH = 'app/data/TRANSCRIPT_Data.csv'
    TRANSCRIPTS_FOLDER = '/Users/chuchun/Downloads/Transcript'
    BUCKET_NAME = 'tsmccareerhack2025-bsid-grp5-bucket'
    
    handler = TranscriptStorageHandler(
        bucket_name=BUCKET_NAME,
        service_account_path='token/tsmccareerhack2025-bsid-grp5-45db6db4b850.json'
    )
    
    # Test getting a URL
    url = handler.get_transcript_url('Apple', '2020', 'Q1')
    if url:
        print(f"Access transcript at: {url}")
    else:
        print("Transcript not found")
        

if __name__ == "__main__":
    main()