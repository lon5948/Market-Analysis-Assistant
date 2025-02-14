import pandas as pd
import numpy as np
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import json

def create_content(row):
    """Create formatted content string from row data"""
    return f"""
    Company: {row['Company Name']}
    Year: {row['CALENDAR_YEAR']}
    Quarter: {row['CALENDAR_QTR']}
    """

def get_embedding(text):
    """Get embedding from Vertex AI TextEmbedding Model"""
    model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values if embeddings else None

def process_transcript_data(input_csv, output_csv):
    # Read the original CSV
    df = pd.read_csv(input_csv)

    # Create new dataframe with required columns
    new_df = pd.DataFrame()

    # Generate sequential IDs
    new_df['id'] = range(10000, len(df) + 10000)

    # Map existing columns
    new_df['company'] = df['Company Name']
    new_df['year'] = df['CALENDAR_YEAR']

    # Convert quarter from 'Q1' format to integer
    new_df['quarter'] = df['CALENDAR_QTR'].str.extract('(\d+)').astype(int)

    # Set constant filename
    new_df['filename'] = df['Transcript_Filename']

    # Generate content
    new_df['content'] = df.apply(create_content, axis=1)

    # Generate embeddings
    print("Generating embeddings... This may take a while...")
    new_df['embedding'] = new_df['content'].apply(get_embedding)

    # Save to CSV
    # Convert embedding arrays to strings for CSV storage
    new_df['embedding'] = new_df['embedding'].apply(lambda x: json.dumps(x) if x is not None else None)
    new_df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")

    return new_df

if __name__ == "__main__":
    df = process_transcript_data('./TRANSCRIPT_data/GLOBAL_TRANSCRIPT_Data.csv', './transcript_embedding_data/global_vector_db_data.csv')

    # Print sample of the processed data
    print("\nSample of processed data:")
    print(df.head(1).to_string())
