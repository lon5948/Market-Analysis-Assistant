# vis.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
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
        role = current_user.role.upper()
        data_path = os.path.join('data', f'{role}_FIN_Data.csv')

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

        role = current_user.role.upper()
        data_path = os.path.join('data', f'{role}_FIN_Data.csv')

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
        colors = [
            '#388E8E',  # Dark Cyan
            '#FF7F50',  # Coral
            '#9932CC',  # Dark Orchid
            '#FFD700',  # Gold
            '#4682B4',  # Steel Blue
            '#CD853F',  # Peru
            '#8B4513',  # Saddle Brown
            '#556B2F',  # Dark Olive Green
            '#8FBC8F',  # Dark Sea Green
            '#B22222',  # Firebrick
            '#6B8E23',  # Olive Drab
            '#8B0000',  # Dark Red
            '#483D8B',  # Dark Slate Blue
            '#2F4F4F',  # Dark Slate Gray
            '#8B008B'   # Dark Magenta
        ]

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
                data = df_yearly.groupby(['CALENDAR_YEAR', 'CALENDAR_QTR'])[index].sum().tolist()
                diff = [0]
                for idx in range(1, len(data)):
                    diff.append((data[idx] - data[idx - 1]) / data[idx - 1] * 100)
                dataset.append({
                    'type': 'line',
                    'label': f'{c} {index} (QoQ % Change)',
                    'data': diff,
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1,
                    'yAxisID': 'y2',
                })
                i += 1
                dataset.append({
                    'label': f'{c} {index}',
                    'data': df_yearly.groupby(['CALENDAR_YEAR', 'CALENDAR_QTR'])[index].sum().tolist(),
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1,
                    'yAxisID': 'y1',
                })
            else:
                data = df_yearly.groupby('CALENDAR_YEAR')[index].sum().tolist()
                diff = [0]
                for idx in range(1, len(data)):
                    if data[idx - 1] == 0:
                        diff.append(0)
                    else:
                        diff.append((data[idx] - data[idx - 1]) / data[idx - 1] * 100)
                dataset.append({
                    'type': 'line',
                    'label': f'{c} {index} (YoY % Change)',
                    'data': diff,
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1,
                    'yAxisID': 'y2',
                })
                i += 1
                dataset.append({
                    'label': f'{c} {index}',
                    'data': df_yearly.groupby('CALENDAR_YEAR')[index].sum().tolist(),
                    'fill': False,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.1,
                    'yAxisID': 'y1',
                })
        
        dataset.sort(key=lambda x: 0 if 'type' in x.keys() else 1)

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
