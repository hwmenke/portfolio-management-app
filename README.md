# Financial Portfolio Management Web Application

A full-stack web application for managing and analyzing financial portfolios using React and FastAPI.

## Features

- Yahoo Finance and Google Finance data scraping
- Portfolio management with Excel upload and manual entry
- Statistical analysis (P&L, VaR, Volatility, Factor Models)
- Interactive dashboard with charts and tables
- PDF report generation

## Setup Instructions

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Project Structure
```
.
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── scraper.py
│   └── analysis.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── requirements.txt
└── README.md
```
