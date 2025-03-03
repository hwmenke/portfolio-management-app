from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import pandas as pd
import json
from datetime import datetime, timedelta
import os

from .models import Portfolio, Position
from .scraper import YahooFinanceScraper, GoogleFinanceScraper
from .analysis import PortfolioAnalyzer

app = FastAPI(title="Portfolio Management API", root_path="/api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scrapers and analyzer
yahoo_scraper = YahooFinanceScraper()
google_scraper = GoogleFinanceScraper()
analyzer = PortfolioAnalyzer()

# In-memory storage (replace with proper database in production)
portfolios = {}

@app.post("/upload")
async def upload_portfolio(file: UploadFile = File(...), user_id: str = None):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    try:
        df = pd.read_excel(await file.read())
        required_columns = ["Ticker", "Shares", "Purchase Price"]
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="Invalid Excel format")
        
        positions = [
            Position(ticker=row["Ticker"], 
                    shares=float(row["Shares"]), 
                    purchase_price=float(row["Purchase Price"]))
            for _, row in df.iterrows()
        ]
        
        portfolios[user_id] = Portfolio(positions=positions)
        return {"message": "Portfolio uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/manual-entry")
async def manual_entry(positions: List[Dict], user_id: str):
    try:
        portfolio_positions = [
            Position(ticker=pos["ticker"], 
                    shares=float(pos["shares"]), 
                    purchase_price=float(pos["price"]))
            for pos in positions
        ]
        portfolios[user_id] = Portfolio(positions=portfolio_positions)
        return {"message": "Portfolio created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data")
async def get_portfolio_data(user_id: str):
    if user_id not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = portfolios[user_id]
    try:
        # Fetch market data
        for position in portfolio.positions:
            yahoo_data = yahoo_scraper.get_stock_data(position.ticker)
            google_data = google_scraper.get_stock_data(position.ticker)
            position.current_price = yahoo_data["current_price"]
            position.market_value = position.current_price * position.shares
            position.unrealized_pl = position.market_value - (position.purchase_price * position.shares)
        
        # Calculate portfolio metrics
        metrics = analyzer.calculate_metrics(portfolio)
        
        return {
            "portfolio": portfolio.dict(),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report")
async def generate_report(user_id: str):
    if user_id not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    try:
        portfolio = portfolios[user_id]
        metrics = analyzer.calculate_metrics(portfolio)
        report_path = analyzer.generate_pdf_report(portfolio, metrics)
        return FileResponse(report_path, filename="portfolio_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
