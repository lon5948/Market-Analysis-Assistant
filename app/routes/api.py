from flask import Blueprint, Flask, request, jsonify
import pandas as pd
import os
from google.cloud import storage, aiplatform
from google.oauth2 import service_account
from datetime import datetime, timedelta
from typing import List

api = Blueprint('api', __name__)
class TranscriptStorageHandler:
    def __init__(self):
        """Initialize the storage client and bucket."""
        bucket_name = os.environ.get('BUCKET_NAME')
        service_account_path = os.environ.get('SERVICE_ACCOUNT_PATH')
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

        print(f"Requesting transcript for: {company}, {year}, {quarter}")

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
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

# TODO: Add api route
def vector_search_find_neighbors(
    index_endpoint_name: str,
    deployed_index_id: str,
    queries: List[List[float]],
    project: str = "tsmccareerhack2025-bsid-grp5",
    location: str = "us-central1",
    num_neighbors: int = 10,
) -> List[
    List[aiplatform.matching_engine.matching_engine_index_endpoint.MatchNeighbor]
]:
    """Query the vector search index.

    Args:
        project (str): Required. Project ID
        location (str): Required. The region name
        index_endpoint_name (str): Required. Index endpoint to run the query
        against.
        deployed_index_id (str): Required. The ID of the DeployedIndex to run
        the queries against.
        queries (List[List[float]]): Required. A list of queries. Each query is
        a list of floats, representing a single embedding.
        num_neighbors (int): Required. The number of neighbors to return.

    Returns:
        List[List[aiplatform.matching_engine.matching_engine_index_endpoint.MatchNeighbor]] - A list of nearest neighbors for each query.
    """
    # Initialize the Vertex AI client
    aiplatform.init(project=project, location=location)

    # Create the index endpoint instance from an existing endpoint.
    my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=index_endpoint_name
    )

    # Query the index endpoint for the nearest neighbors.
    return my_index_endpoint.find_neighbors(
        deployed_index_id=deployed_index_id,
        queries=queries,
        num_neighbors=num_neighbors,
    )
