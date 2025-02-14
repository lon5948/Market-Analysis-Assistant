# vis.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import pandas as pd
import os, random

vis = Blueprint('vis', __name__)

@vis.route('/visualization')
@login_required  # Add this if you want to require login
def visualization():
    return render_template('visualization.html')

@vis.route('/api/companies')
@login_required  # Add this if you want to require login
def get_companies():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(os.path.dirname(current_dir), 'data', 'FIN_Data.csv')

        df = pd.read_csv(data_path)
        companies = df['Company Name'].unique().tolist()
        return jsonify({'companies': companies})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vis.route('/api/financial-data')
@login_required  # Add this if you want to require login
def get_financial_data():
    try:
        period = request.args.get('period')
        currency = request.args.get('currency')
        startYear = request.args.get('startYear')
        endYear = request.args.get('endYear')
        company = request.args.get('company')
        index = request.args.get('index')

        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(os.path.dirname(current_dir), 'data', 'FIN_Data.csv')

        # Read your CSV file - adjust the path as needed
        df = pd.read_csv(data_path)

        if currency == 'TWD':
            for idx, row in df.iterrows():
                df.at[idx, 'USD_Value'] = row['USD_Value'] * 32.93
        
        df_pivot = df.pivot(index=["Company Name", "CALENDAR_YEAR", "CALENDAR_QTR"], columns="Index", values="USD_Value").reset_index()

        local_currency = df.groupby(["Company Name", "CALENDAR_YEAR", "CALENDAR_QTR"])["Local_Currency"].first().reset_index()
        val_unit = df.groupby(["Company Name", "CALENDAR_YEAR", "CALENDAR_QTR"])["VAL_UNIT"].first().reset_index()

        # Merge them with the pivoted table
        df_pivot = df_pivot.merge(local_currency, on=["Company Name", "CALENDAR_YEAR", "CALENDAR_QTR"], how="left")
        df_pivot = df_pivot.merge(val_unit, on=["Company Name", "CALENDAR_YEAR", "CALENDAR_QTR"], how="left")
        df_pivot['Gross Profit'] = df_pivot['Revenue'] - df_pivot['Cost of Goods Sold']
        df_pivot["Gross Profit Margin"] = (df_pivot["Revenue"] - df_pivot["Cost of Goods Sold"]) / df_pivot["Revenue"] * 100
        df_pivot["Operating Margin"] = df_pivot["Operating Income"] / df_pivot["Revenue"] * 100
        # print(df_pivot.head())

        


        if startYear and endYear:
            df_pivot = df_pivot[(df_pivot['CALENDAR_YEAR'] >= int(startYear)) & (df_pivot['CALENDAR_YEAR'] <= int(endYear))]
        
        dataset = []
        
        # 15 colors
        colors = ['#4bc0c0', '#FFB399', '#FF33FF', '#FFFF99', '#00B3E6',
                  '#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
                  '#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A']

        i = -1
        for c in company.split(','):
            if c not in df_pivot['Company Name'].unique():
                continue
            i += 1
            df_yearly = df_pivot[df_pivot['Company Name'] == c]
            
            if period == 'quarterly':
                df_yearly = df_yearly.groupby(['CALENDAR_YEAR', 'CALENDAR_QTR']).agg({
                    'Cost of Goods Sold': 'sum',
                    'Operating Expense': 'sum',
                    'Operating Income': 'sum',
                    'Revenue': 'sum',
                    'Tax Expense': 'sum',
                    'Total Asset': 'last',
                    'Gross Profit': 'sum',
                }).reset_index()
            else:
                df_yearly = df_yearly.groupby('CALENDAR_YEAR').agg({
                    'Cost of Goods Sold': 'sum',
                    'Operating Expense': 'sum',
                    'Operating Income': 'sum',
                    'Revenue': 'sum',
                    'Tax Expense': 'sum',
                    'Total Asset': 'last',
                    'Gross Profit': 'sum',
                }).reset_index()

            df_yearly['Gross Profit Margin'] = (df_yearly['Gross Profit'] / df_yearly['Revenue']) * 100
            df_yearly['Operating Margin'] = (df_yearly['Operating Income'] / df_yearly['Revenue']) * 100
            # 10 colors

            # print(df_yearly.head())

            if period == 'quarterly':
                dataset.append({
                    'label': c,
                    'data': df_yearly.groupby(['CALENDAR_YEAR', 'CALENDAR_QTR'])[index].sum().tolist(),
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1
                })
            else:
                dataset.append({
                    'label': c,
                    'data': df_yearly.groupby('CALENDAR_YEAR')[index].sum().tolist(),
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1
                })
        
        if len(dataset) == 0:
            return jsonify({'error': 'No data found for the selected company'}), 404

        if period == 'quarterly':
            data = {
                'labels': (df_yearly['CALENDAR_YEAR'].astype(str) + ' ' + df_yearly['CALENDAR_QTR'].astype(str)).tolist(),
                'datasets': dataset
            }
        else:
            data = {
                'labels': df_yearly['CALENDAR_YEAR'].unique().tolist(),
                'datasets': dataset
            }
        # print(data)
        return jsonify(data)
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500