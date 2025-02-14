# Market Analysis Assistant

An AI-powered market analysis tool that provides real-time financial data insights and support through natural language interactions.

## Features
- [x] User account creation and management
- [ ] Role-based data access control
- [ ] Data visualization
- [ ] Financial chatbot with natural language processing
- [ ] Financial report summarization

## Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lon5948/market-analysis-assistant.git
cd market-analysis-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy the `.env.example` file to `.env`
- Fill in your configuration values:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Running the Application

1. Install playwright
```bash
playwright install
```
2. Initialize the database:
```bash
python migrations.py
```
3. Start the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Project Structure
- `app/` - Main application package
  - `models/` - Database models
  - `routes/` - Application routes and views
  - `templates/` - HTML templates
- `migrations/` - Database migrations
- `config.py` - Application configuration
- `requirements.txt` - Python dependencies
- `run.py` - Application entry point

## Available Roles
- Korea Data Viewer: Access to Korean company data
- China Data Viewer: Access to Chinese company data
- Global Data Viewer: Access to all company data
- None
