from google.cloud.aiplatform.matching_engine import MatchingEngineIndex
from google.cloud import aiplatform
from google.cloud.aiplatform_v1 import IndexDatapoint
import csv
import pandas as pd

def get_datapoints(country):
    embedding_file = f'../embedding_data/{country}_vector_db_data.csv'
    transcript_file = f'../transcript_embedding_data/{country}_vector_db_data.csv'

    embedding_df = pd.read_csv(embedding_file)
    transcript_df = pd.read_csv(transcript_file)

    embedding_datapoints = embedding_df.iloc[:, [0, -1]].values.tolist()
    transcript_datapoints = transcript_df.iloc[:, [0, -1]].values.tolist()

    datapoints = embedding_datapoints + transcript_datapoints

    index_datapoints = [IndexDatapoint(datapoint_id=str(item[0]), feature_vector=eval(item[1])) for item in datapoints]
    return index_datapoints

def upload_datapoints(index: MatchingEngineIndex, index_datapoints: list[IndexDatapoint]):
    for i in range(0, len(index_datapoints), 1000):
        index.upsert_datapoints(index_datapoints[i:i+1000])

index_idx = {
    "korea": "62412678039076864",
    # "china": "2648604764056584192",
    "global": "2745432156045049856"
}

for country in index_idx:
    index_id = index_idx[country]
    index = MatchingEngineIndex(index_name=index_id)
    upload_datapoints(index, get_datapoints(country))
