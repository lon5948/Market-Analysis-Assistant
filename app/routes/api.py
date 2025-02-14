from flask import Blueprint, request, jsonify, redirect
import pandas as pd
import os
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime, timedelta

api = Blueprint('api', __name__)
class TranscriptStorageHandler:
    def __init__(self):
        """Initialize the storage client and bucket."""
        try:
            bucket_name = os.environ.get('BUCKET_NAME')
            service_account_path = os.environ.get('SERVICE_ACCOUNT_PATH')
            print(f"Initializing with bucket: {bucket_name}")
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            self.storage_client = storage.Client(credentials=credentials)
            self.bucket = self.storage_client.bucket(bucket_name)
            
            # Test bucket access
            try:
                self.bucket.reload()
                print("Successfully connected to bucket")
            except exceptions.Forbidden as e:
                print(f"Permission denied accessing bucket: {str(e)}")
                raise
                
            self.credentials = credentials
        except Exception as e:
            print(f"Error in initialization: {type(e).__name__}: {str(e)}")
            raise

    def get_transcript_content(self, company, year, quarter):
        """
        Fetch the content of a transcript file from GCP Storage.
        """
        try:
            # Format the quarter to ensure consistency
            quarter = f"Q{quarter}" if not str(quarter).startswith('Q') else str(quarter)
            prefix = f"metadata/transcripts/{company}/{year}/{quarter}/"
            print(f"Searching for transcript in: {prefix}")
            
            try:
                # List blobs with the prefix
                blobs = list(self.bucket.list_blobs(prefix=prefix, max_results=1))
                print(f"Successfully listed blobs in {prefix}")
            except exceptions.Forbidden as e:
                print(f"Permission denied listing blobs: {str(e)}")
                return None, f"Permission denied accessing files: {str(e)}"
            
            if not blobs:
                return None, f"No transcript found for {company} {year} {quarter}"
            
            blob = blobs[0]
            print(f"Found transcript file: {blob.name}")
            
            try:
                # Download and decode the content
                content = blob.download_as_string().decode('utf-8')
                print("Successfully downloaded content")
                return content, None
            except exceptions.Forbidden as e:
                print(f"Permission denied downloading file: {str(e)}")
                return None, f"Permission denied downloading file: {str(e)}"
            
        except Exception as e:
            error_msg = f"Error type: {type(e).__name__}, Message: {str(e)}"
            print(f"Error fetching transcript: {error_msg}")
            return None, error_msg
        
    def upload_transcript(self, file_path, company, year, quarter):
        """Upload a transcript file to GCP Storage."""
        blob_path = f"metadata/transcripts/{company}/{year}/{quarter}/{os.path.basename(file_path)}"
        blob = self.bucket.blob(blob_path)
        blob.upload_from_filename(file_path)
        return blob_path

    def get_transcript_url(self, company, year, quarter):
        """Generate a signed URL for accessing the transcript."""
        try:
            prefix = f"metadata/transcripts/{company}/{year}/{quarter}/"
            blobs = list(self.bucket.list_blobs(prefix=prefix, max_results=1))
            if not blobs:
                return None
            blob = blobs[0]
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(hours=1),
                service_account_email=self.credentials.service_account_email,
                access_token=None,
                credentials=self.credentials
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating signed URL: {str(e)}")
        
    
@api.route('/api/upload_transcripts', methods=['POST'])
def upload_transcripts():
    data = request.json
    csv_path = data.get('csv_path')
    transcripts_folder = data.get('transcripts_folder')

    handler = TranscriptStorageHandler()
    df = pd.read_csv(csv_path)
    successful, failed = 0, 0
    failed_files = []

    for index, row in df.iterrows():
        try:
            company = row['Company Name']
            year = str(row['CALENDAR_YEAR'])
            quarter = str(row['CALENDAR_QTR'])
            filename = f"{row['Transcript_Filename']}.txt"
            transcript_path = os.path.join(transcripts_folder, filename)
            if not os.path.exists(transcript_path):
                failed += 1
                failed_files.append(filename)
                continue
            handler.upload_transcript(transcript_path, company, year, quarter)
            successful += 1
        except Exception as e:
            failed += 1
            failed_files.append(filename)

    return jsonify({
        "successful": successful,
        "failed": failed,
        "failed_files": failed_files
    })

@api.route('/api/get_transcript_url', methods=['POST', 'GET'])
def get_transcript_url():
    """
    request example:

    payload = json.dumps({
        "company": "Apple",
        "year": "2020",
        "quarter": "Q1"
        })
        headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    """
    try:
        if request.method == 'GET':
            company = request.args.get('company')
            year = request.args.get('year')
            quarter = request.args.get('quarter')
            
            # Validate inputs
            if not all([company, year, quarter]):
                return jsonify({
                    "error": "Missing required parameters",
                    "required": ["company", "year", "quarter"],
                    "received": {
                        "company": company,
                        "year": year,
                        "quarter": quarter
                    }
                }), 400
            
            handler = TranscriptStorageHandler()
            url = handler.get_transcript_url(company, year, quarter)
            
            if url:
                return redirect(url)  # Redirect to the actual transcript
            else:
                return "Transcript not found", 404  # Simple text response for browser
                
        # Handle POST request (from curl/postman)
        else:
            data = request.json
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
                
            company = data.get('company')
            year = data.get('year')
            quarter = data.get('quarter')
            
            # Validate inputs
            if not all([company, year, quarter]):
                return jsonify({
                    "error": "Missing required fields",
                    "required": ["company", "year", "quarter"],
                    "received": data
                }), 400
            
            handler = TranscriptStorageHandler()
            url = handler.get_transcript_url(company, year, quarter)
            
            if url:
                return jsonify({"url": url})
            else:
                return jsonify({
                    "error": "Transcript not found",
                    "details": {
                        "company": company,
                        "year": year,
                        "quarter": quarter
                    }
                }), 404
            
    except Exception as e:
        print(f"Error in API endpoint: {str(e)}")
        if request.method == 'GET':
            return f"Error: {str(e)}", 500  # Simple text response for browser
        else:
            return jsonify({
                "error": "Internal server error",
                "details": str(e)
            }), 500

@api.route('/api/fetch_transcript_content', methods=['POST'])
def fetch_transcript_content():
    """
    Endpoint to fetch the content of a transcript file.
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Extract parameters
        company = data.get('company')
        year = data.get('year')
        quarter = data.get('quarter')
        
        # Validate required fields
        if not all([company, year, quarter]):
            return jsonify({
                "error": "Missing required fields",
                "required": ["company", "year", "quarter"],
                "received": data
            }), 400
        
        print(f"Fetching transcript for {company} {year} {quarter}")
        
        # Initialize handler and fetch content
        try:
            handler = TranscriptStorageHandler()
        except Exception as e:
            return jsonify({
                "error": "Failed to initialize storage handler",
                "details": str(e)
            }), 500
        
        content, error = handler.get_transcript_content(company, year, quarter)
        
        if error:
            return jsonify({
                "error": error,
                "details": {
                    "company": company,
                    "year": year,
                    "quarter": quarter
                }
            }), 403 if "Permission denied" in error else 404
        
        return jsonify({
            "company": company,
            "year": year,
            "quarter": quarter,
            "content": content
        })
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500