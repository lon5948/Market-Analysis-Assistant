# vis.py
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
import pandas as pd

vis = Blueprint('vis', __name__)

@vis.route('/visualization')
@login_required  # Add this if you want to require login
def visualization():
    return render_template('visualization.html')

@vis.route('/api/financial-data')
@login_required  # Add this if you want to require login
def get_financial_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(os.path.dirname(current_dir), 'data', 'FIN_Data.csv')

        # Read your CSV file - adjust the path as needed
        df = pd.read_csv(data_path)
        
        # Example: Process data for Chart.js
        data = {
            'labels': df['Calendar Year'].unique().tolist(),
            'datasets': [{
                'label': 'Revenue',
                'data': df.groupby('Calendar Year')['Value (USD)'].sum().tolist(),
                'fill': False,
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500