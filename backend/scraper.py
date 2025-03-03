import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class YahooFinanceScraper:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)

    def get_stock_data(self, ticker: str) -> dict:
        now = datetime.now()
        if ticker in self.cache:
            cached_data, timestamp = self.cache[ticker]
            if now - timestamp < self.cache_duration:
                return cached_data

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            info = stock.info

            data = {
                "current_price": info.get("regularMarketPrice", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("forwardPE", 0),
                "beta": info.get("beta", 1),
                "historical_data": hist.to_dict("records"),
                "returns": hist["Close"].pct_change().dropna().tolist()
            }

            self.cache[ticker] = (data, now)
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch Yahoo Finance data for {ticker}: {str(e)}")

class GoogleFinanceScraper:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)

    def get_stock_data(self, ticker: str) -> dict:
        now = datetime.now()
        if ticker in self.cache:
            cached_data, timestamp = self.cache[ticker]
            if now - timestamp < self.cache_duration:
                return cached_data

        try:
            url = f"https://www.google.com/finance/quote/{ticker}:NASDAQ"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            data = {
                "price": self._extract_price(soup),
                "52w_range": self._extract_52w_range(soup),
                "analyst_rating": self._extract_analyst_rating(soup)
            }

            self.cache[ticker] = (data, now)
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch Google Finance data for {ticker}: {str(e)}")

    def _extract_price(self, soup):
        try:
            price_div = soup.find("div", {"class": "YMlKec fxKbKc"})
            return float(price_div.text.replace("$", "").replace(",", "")) if price_div else None
        except:
            return None

    def _extract_52w_range(self, soup):
        try:
            range_div = soup.find("div", text="52-week range").parent
            return range_div.find_all("div")[1].text if range_div else None
        except:
            return None

    def _extract_analyst_rating(self, soup):
        try:
            rating_div = soup.find("div", text="Analyst rating").parent
            return rating_div.find_all("div")[1].text if rating_div else None
        except:
            return None
