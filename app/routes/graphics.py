from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
import pandas as pd
import numpy as np
import os
from PIL import Image
from matplotlib import pyplot as plt

from playwright.sync_api import sync_playwright

graphics = Blueprint('graphics', __name__)

@graphics.route('/api/graphics')
@login_required  # Add this if you want to require login
def get_graphics():
    try:
        role = current_user.role.upper()
        role = 'GLOBAL' if role == 'ADMIN' else role
        data_path = os.path.join('data', f'{role}_FIN_Data.csv')

        company = request.args.get('company')
        year = request.args.get('year')
        quarter = request.args.get('quarter')

        if year == '2020' and quarter == '1':
            prev_year = '2020'
            prev_quarter = '1'
        elif quarter == '1':
            prev_year = str(int(year) - 1)
            prev_quarter = '4'
        else:
            prev_year = year
            prev_quarter = str(int(quarter) - 1)
    

        print(company, year, quarter, prev_year, prev_quarter)

        df = pd.read_csv(data_path)

        cur_df = df[(df['Company Name'] == company) & (df['CALENDAR_YEAR'] == int(year)) & (df['CALENDAR_QTR'] == f'Q{quarter}')]
        prev_df = df[(df['Company Name'] == company) & (df['CALENDAR_YEAR'] == int(prev_year)) & (df['CALENDAR_QTR'] == f'Q{prev_quarter}')]

        # print(cur_df.head())
        # print(prev_df.head())

        revenue = cur_df[(cur_df['Index'] == 'Revenue')]['USD_Value'].values[0]
        cogs = cur_df[(cur_df['Index'] == 'Cost of Goods Sold')]['USD_Value'].values[0]
        op_expense = cur_df[(cur_df['Index'] == 'Operating Expense')]['USD_Value'].values[0]
        op_income = cur_df[(cur_df['Index'] == 'Operating Income')]['USD_Value'].values[0]
        gross_profit = revenue - cogs
        tax_expense = cur_df[(cur_df['Index'] == 'Tax Expense')]['USD_Value'].values[0]
        total_asset = cur_df[(cur_df['Index'] == 'Total Asset')]['USD_Value'].values[0]
        gross_profit_margin = (gross_profit / revenue) * 100
        op_margin = (op_income / revenue) * 100

        prev_revenue = prev_df[(prev_df['Index'] == 'Revenue')]['USD_Value'].values[0]
        prev_cogs = prev_df[(prev_df['Index'] == 'Cost of Goods Sold')]['USD_Value'].values[0]
        prev_op_expense = prev_df[(prev_df['Index'] == 'Operating Expense')]['USD_Value'].values[0]
        prev_op_income = prev_df[(prev_df['Index'] == 'Operating Income')]['USD_Value'].values[0]
        prev_gross_profit = prev_revenue - prev_cogs
        prev_tax_expense = prev_df[(prev_df['Index'] == 'Tax Expense')]['USD_Value'].values[0]
        prev_total_asset = prev_df[(prev_df['Index'] == 'Total Asset')]['USD_Value'].values[0]
        prev_gross_profit_margin = (prev_gross_profit / prev_revenue) * 100
        prev_op_margin = (prev_op_income / prev_revenue) * 100

        values = {
            'Revenue': revenue,
            'Cost of Goods Sold': cogs,
            'Operating Expense': op_expense,
            'Operating Income': op_income,
            'Gross Profit': gross_profit,
            'Tax Expense': tax_expense,
            'Total Asset': total_asset,
            'Gross Profit Margin': gross_profit_margin,
            'Operating Margin': op_margin
        }

        prev_values = {
            'Revenue': prev_revenue,
            'Cost of Goods Sold': prev_cogs,
            'Operating Expense': prev_op_expense,
            'Operating Income': prev_op_income,
            'Gross Profit': prev_gross_profit,
            'Tax Expense': prev_tax_expense,
            'Total Asset': prev_total_asset,
            'Gross Profit Margin': prev_gross_profit_margin,
            'Operating Margin': prev_op_margin
        }

        categories = values.keys()
        values1 = list(values.values())
        values2 = list(prev_values.values())
        units = ['$'] * 7 + ['%'] * 2

        x = np.arange(len(categories)) * 1
        width = 0.35

        fig, ax1 = plt.subplots(figsize=(20, 10))
        ax2 = ax1.twinx()

        # print(values1, values2)

        # Create bar chart
        bar1 = ax1.bar(x[:-2] - width/2, values1[:-2], width, label='This quarter', color='skyblue')
        bar2 = ax1.bar(x[:-2] + width/2, values2[:-2], width, label='Last quarter', color='salmon')

        # Create bar chart for the percentage value
        ax2.bar(x[-2:] - width/2, values1[-2:], width, color='skyblue')
        ax2.bar(x[-2:] + width/2, values2[-2:], width, color='salmon')

        # Add labels and title
        ax1.set_ylabel('Millon USD', color='black', fontsize=20)
        ax2.set_ylabel('Percentage (%)', color='black', fontsize=20)
        ax1.set_title('metrics comparison', fontsize=32)
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{cat} ({unit})' for cat, unit in zip(categories, units)], fontsize=16, rotation=10)

        # Set font size for y-axis tick labels
        ax1.tick_params(axis='y', labelsize=16)
        ax2.tick_params(axis='y', labelsize=16)

        bars = [bar1, bar2]
        ax1.legend([b.get_label() for b in bars], loc='upper left', fontsize=16)
        # Show the plot
        plt.savefig('app/images/grouped_bar_chart.png', dpi=300)

        formats = [f"{company} {year} Q{quarter}"]
        for key, value in values.items():
            prev_value = prev_values[key]
            change = ((value - prev_value) / prev_value) * 100
            change = round(change, 2)
            color = 'lightgreen' if change > 0 else 'lightcoral'
            color = 'white' if change == 0 else color
            change = f'+{change}' if change > 0 else str(change)
            formats += [value, prev_value, color , change]
        
        html = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9f5f0; }
                .container { background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .date { font-weight: bold; }
                table { width: 100%%; border-collapse: collapse; margin-top: 10px; }
                th, td { padding: 10px; border: 1px solid #ddd; text-align: center; }
                th { background-color: #b22222; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>%s Financial Report</h1>
                <h2>Key Metrics Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>This Quarter</th>
                            <th>Last Quarter</th>
                            <th>%% Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Revenue</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Cost of Goods Sold (COGS)</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Operating Expense</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Operating Income</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Gross Profit</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Tax Expense</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Total Asset</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Gross Profit Margin</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                        <tr>
                            <td>Operating Margin</td>
                            <td>$%d</td>
                            <td>$%d</td>
                            <td style="background-color: %s;">%s%%</td>
                        </tr>
                    </tbody>
                </table>
                </img>
                <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
                <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
            </div>
        </body>
        </html>
        ''' % tuple([*formats])
        # print(html)


        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            page.screenshot(path=os.path.join(os.getcwd(), "app/images/financial_report.png"), full_page=True)
            browser.close()

        # print(df)
        # Open the background and overlay images
        background = Image.open("app/images/financial_report.png")
        overlay = Image.open("app/images/grouped_bar_chart.png")
        
        scale = 0.2
        overlay = overlay.resize((int(overlay.width * scale), int(overlay.height * scale)))

        # Set position (top-left corner)
        position = ((background.width - overlay.width) // 2, 600)

        # Paste overlay on background (with transparency if PNG)
        background.paste(overlay, position, overlay)

        # Save or show the result
        background.save("app/images/financial_report.png")

        return send_file('images/financial_report.png', mimetype='image/png')
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500