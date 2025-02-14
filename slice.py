import pandas as pd

# Read the CSV file
df = pd.read_csv('app/data/FIN_Data.csv')

# Calculate Gross Profit Margin (%) using Local Value
gross_profit_margin = df[df['Index'] == 'Revenue'].copy()
gross_profit_margin['Index'] = 'Gross Profit Margin (%)'
gross_profit_margin['Local_Value'] = ((df[df['Index'] == 'Revenue']['Local_Value'].values - df[df['Index'] == 'Cost of Goods Sold']['Local_Value'].values) / df[df['Index'] == 'Revenue']['Local_Value'].values) * 100
gross_profit_margin['USD_Value'] = gross_profit_margin['Local_Value']

# Calculate Operating Margin (%) using Local Value
operating_margin = df[df['Index'] == 'Revenue'].copy()
operating_margin['Index'] = 'Operating Margin (%)'
operating_margin['Local_Value'] = (df[df['Index'] == 'Operating Income']['Local_Value'].values / df[df['Index'] == 'Revenue']['Local_Value'].values) * 100
operating_margin['USD_Value'] = operating_margin['Local_Value']

# Append the new rows to the original dataframe
df = pd.concat([df, gross_profit_margin, operating_margin])

# Check for Local_Currency and save data into separate files
df_krw = df[df['Local_Currency'] == 'KRW']
df_cny = df[df['Local_Currency'] == 'CNY']

# Save Korean data to KRW_FIN_Data.csv
if not df_krw.empty:
    df_krw.to_csv('KRW_FIN_Data.csv', index=False)

# Save Chinese data to CNY_FIN_Data.csv
if not df_cny.empty:
    df_cny.to_csv('CNY_FIN_Data.csv', index=False)

# Save the entire data to GLOBAL_FIN_Data.csv
df.to_csv('GLOBAL_FIN_Data.csv', index=False)
