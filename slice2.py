import pandas as pd

# Read the CSV files
fin_df = pd.read_csv('app/data/FIN_Data.csv')
transcript_df = pd.read_csv('app/data/TRANSCRIPT_Data.csv')

# Merge the dataframes on 'Company Name'
merged_df = pd.merge(transcript_df, fin_df[['Company Name', 'Local_Currency']], on='Company Name', how='left').drop_duplicates()

# Check for Local_Currency and save data into separate files
df_krw = merged_df[merged_df['Local_Currency'] == 'KRW']
df_cny = merged_df[merged_df['Local_Currency'] == 'CNY']

# Save Korean data to KRW_TRANSCRIPT_Data.csv
if not df_krw.empty:
    df_krw.to_csv('KRW_TRANSCRIPT_Data.csv', index=False)

# Save Chinese data to CNY_TRANSCRIPT_Data.csv
if not df_cny.empty:
    df_cny.to_csv('CNY_TRANSCRIPT_Data.csv', index=False)

# Save the entire data to GLOBAL_TRANSCRIPT_Data.csv
merged_df.to_csv('GLOBAL_TRANSCRIPT_Data.csv', index=False)
