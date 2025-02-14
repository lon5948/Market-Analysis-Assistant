import csv
import pandas as pd

countries = ["korea", "china", "global"]

def combine_embeddings():
    for country in countries:
        embedding_file = f'../embedding_data/{country}_vector_db_data.csv'
        transcript_file = f'../transcript_embedding_data/{country}_vector_db_data.csv'

        embedding_df = pd.read_csv(embedding_file)
        transcript_df = pd.read_csv(transcript_file)

        # append the transcript embeddings to the embedding embeddings
        combined_df = pd.concat([embedding_df, transcript_df], axis=0)
        import os
        if not os.path.exists('../combined_embedding_data'):
            os.makedirs('../combined_embedding_data')
        combined_df.to_csv(f'../combined_embedding_data/{country}_combined_vector_db_data.csv', index=False)

combine_embeddings()
