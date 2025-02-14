# chat.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from vertexai.preview.language_models import TextEmbeddingModel
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import aiplatform
from typing import List
import csv
import os

chat = Blueprint('chat', __name__)
class FinancialChatbot:
    def __init__(self, project, location, embedding_model, generative_model):
        """Initialize the FinancialChatbot with project settings.

        Args:
            project (str): GCP project ID
            location (str): GCP region
        """
        self.project = project
        self.location = location
        aiplatform.init(project=project, location=location)
        self.embedding_model = TextEmbeddingModel.from_pretrained(embedding_model)
        self.generative_model = GenerativeModel(generative_model)

    def get_datapoint_content_from_csv(self, file_path: str, id: int) -> List[str]:
        """Read content from CSV file for a specific row."""
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                try:
                    if int(row[0]) == id:
                        return row[:-1]
                except ValueError:
                    continue
        return []

    def vector_search_find_neighbors(
        self,
        index_endpoint_name: str,
        deployed_index_id: str,
        queries: List[List[float]],
        num_neighbors: int = 10
    ) -> List[List[aiplatform.matching_engine.matching_engine_index_endpoint.MatchNeighbor]]:
        """Perform vector search to find nearest neighbors."""
        my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoint_name
        )
        return my_index_endpoint.find_neighbors(
            deployed_index_id=deployed_index_id,
            queries=queries,
            num_neighbors=num_neighbors,
        )

    def perform_vector_search_and_get_content(
        self,
        input_string: str,
        lookup_file: str,
        index_endpoint_name: str,
        deployed_index_id: str
    ) -> List[List[str]]:
        """Get content based on vector search results."""
        embeddings = self.embedding_model.get_embeddings([input_string])
        neighbors = self.vector_search_find_neighbors(
            index_endpoint_name=index_endpoint_name,
            deployed_index_id=deployed_index_id,
            queries=[embeddings[0].values],
        )

        content = []
        for neighbor in neighbors[0]:
            content.append(self.get_datapoint_content_from_csv(lookup_file, int(neighbor.id)))
        return content

    def generate_response(
        self,
        input_string: str,
        lookup_file: str,
        index_endpoint_name: str,
        deployed_index_id: str,
        prompt_template: str = None
    ) -> str:
        """Generate response based on user input and context."""
        if prompt_template is None:
            prompt_template = """You are a financial analyst. You are being asked for the given input:

            {input}

            You are analyzing based on the following financial data:

            {content}
            """

        contexts = self.perform_vector_search_and_get_content(
            input_string, lookup_file, index_endpoint_name, deployed_index_id
        )

        prompt = prompt_template.format(
            input=input_string,
            content="\n\n".join([context[5] for context in contexts if context])
        )
        response = self.generative_model.generate_content(prompt)
        return response.text

# Initialize chatbot
project = os.environ.get("PROJECT")
location = os.environ.get("VECTOR_SEARCH_LOCATION")
embedding_model = os.environ.get("EMBEDDING_MODEL")
generative_model = os.environ.get("GENERATIVE_MODEL")
chatbot = FinancialChatbot(project, location, embedding_model, generative_model)

@chat.route('/chatbot')
@login_required
def chatbot_page():
    return render_template('chatbot.html')

@chat.route('/api/chat', methods=['POST'])
@login_required
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('message')

        # Get appropriate lookup file and endpoints based on user's role
        cur_role = current_user.role.upper()
        if cur_role == 'ADMIN':
            cur_role = 'GLOBAL'

        if cur_role != 'NONE':
            lookup_file = os.environ.get(f"{cur_role}_LOOKUP_FILES")
            index_endpoint_name = os.environ.get(f"{cur_role}_ENDPOINT")
            deployed_index_id = os.environ.get(f"{cur_role}_DEPLOYED_ID")

            response = chatbot.generate_response(
                input_string=user_message,
                lookup_file=lookup_file,
                index_endpoint_name=index_endpoint_name,
                deployed_index_id=deployed_index_id
            )
            return jsonify({'response': response})

        return jsonify({'message': 'User role not set. Please contact your system administrator'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
