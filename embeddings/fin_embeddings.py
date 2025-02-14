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
    Financial Index: {row['Index']}
    Value (USD): ${row['USD_Value']:,.2f}
    Local Currency: {row['Local_Currency']}
    Local Value: {row['Local_Value']:,.2f}
    """

def get_embedding(text):
    """Get embedding from Vertex AI TextEmbedding Model"""
    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
    embeddings = model.get_embeddings([text])
    return embeddings[0].values if embeddings else None

def process_financial_data(input_csv, output_csv):
    # Read the original CSV
    df = pd.read_csv(input_csv)

    # Create new dataframe with required columns
    new_df = pd.DataFrame()

    # Generate sequential IDs
    new_df['id'] = range(1, len(df) + 1)

    # Map existing columns
    new_df['company'] = df['Company Name']
    new_df['year'] = df['CALENDAR_YEAR']

    # Convert quarter from 'Q1' format to integer
    new_df['quarter'] = df['CALENDAR_QTR'].str.extract('(\d+)').astype(int)

    # Set constant filename
    new_df['filename'] = 'FIN'

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
    countries = ['global', 'korea', 'china']
    for country in countries:
        df = process_financial_data(f'./FIN_data/{country.upper()}_FIN_Data.csv', f'./embedding_data/{country}_vector_db_data.csv')
