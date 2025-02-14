# report.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
import pandas as pd
import os

report = Blueprint('report', __name__)

def get_unique_companies_and_years(role):
    """Read CSV and return unique company names"""
    try:
        role = role.upper()
        if role == "ADMIN":
            role = "GLOBAL"
        file_path = os.path.join('data', f'{role}_FIN_Data.csv')
        print(f"Attempting to read file: {file_path}") # Debug log

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}") # Debug log
            return []

        df = pd.read_csv(file_path)
        companies = sorted(df['Company Name'].unique().tolist())
        years = sorted(df['CALENDAR_YEAR'].unique().tolist())
        quarters = sorted(df['CALENDAR_QTR'].unique().tolist())
        return companies, years, quarters
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return []

@report.route('/summary')
@login_required  # Add this if you want to require login
def summary():
    companies, years, quarters = get_unique_companies_and_years(current_user.role)
    return render_template('summary.html', companies=companies, years=years, quarters=quarters)
