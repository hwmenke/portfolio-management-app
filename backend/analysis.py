import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Lasso
from statsmodels.regression.linear_model import OLS
import yfinance as yf
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
from datetime import datetime
from typing import Dict, List

from .models import Portfolio, Position

class PortfolioAnalyzer:
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    def calculate_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate all portfolio metrics"""
        total_value = sum(p.market_value for p in portfolio.positions)
        
        # Calculate position weights
        for position in portfolio.positions:
            position.weight = position.market_value / total_value if total_value > 0 else 0

        # Get historical data for all positions and SPY
        spy = yf.download("SPY", period="2y")["Adj Close"].pct_change().dropna()
        position_returns = []
        
        for position in portfolio.positions:
            hist = yf.download(position.ticker, period="2y")["Adj Close"].pct_change().dropna()
            position_returns.append(hist * position.weight)

        portfolio_returns = pd.concat(position_returns, axis=1).sum(axis=1)

        metrics = {
            "total_value": total_value,
            "daily_pl": self._calculate_daily_pl(portfolio_returns),
            "var_95": self._calculate_var(portfolio_returns),
            "volatility": self._calculate_volatility(portfolio_returns),
            "sharpe_ratio": self._calculate_sharpe_ratio(portfolio_returns),
            "beta": self._calculate_beta(portfolio_returns, spy),
            "lasso_predictions": self._run_lasso(portfolio)
        }

        return metrics

    def _calculate_daily_pl(self, returns: pd.Series) -> float:
        """Calculate daily P&L"""
        if len(returns) > 0:
            return returns.iloc[-1]
        return 0.0

    def _calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk using historical simulation"""
        if len(returns) > 0:
            return np.percentile(returns, (1 - confidence_level) * 100)
        return 0.0

    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        if len(returns) > 0:
            return returns.std() * np.sqrt(252)  # Annualize daily volatility
        return 0.0

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) > 0:
            excess_returns = returns - self.risk_free_rate/252
            return np.sqrt(252) * excess_returns.mean() / returns.std()
        return 0.0

    def _calculate_beta(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate portfolio beta using CAPM"""
        if len(returns) > 0 and len(market_returns) > 0:
            # Align dates
            aligned_data = pd.concat([returns, market_returns], axis=1).dropna()
            if len(aligned_data) > 0:
                X = aligned_data.iloc[:, 1]
                y = aligned_data.iloc[:, 0]
                model = OLS(y, X).fit()
                return model.params[0]
        return 1.0

    def _run_lasso(self, portfolio: Portfolio) -> Dict[str, float]:
        """Run LASSO regression for return prediction"""
        predictions = {}
        
        for position in portfolio.positions:
            try:
                # Get historical data
                stock = yf.download(position.ticker, period="2y")
                
                # Create features (lagged returns, volume, etc.)
                data = pd.DataFrame()
                data["returns"] = stock["Adj Close"].pct_change()
                data["volume"] = stock["Volume"].pct_change()
                data["high_low"] = (stock["High"] - stock["Low"]) / stock["Low"]
                
                # Create lagged features
                for i in range(1, 6):
                    data[f"returns_lag_{i}"] = data["returns"].shift(i)
                    data[f"volume_lag_{i}"] = data["volume"].shift(i)
                
                data = data.dropna()
                
                # Prepare training data
                X = data.drop("returns", axis=1)
                y = data["returns"]
                
                # Fit LASSO
                model = Lasso(alpha=0.01)
                model.fit(X[:-1], y[1:])
                
                # Make prediction
                next_day_pred = model.predict(X.iloc[[-1]])[0]
                predictions[position.ticker] = next_day_pred
                
            except Exception:
                predictions[position.ticker] = 0.0
        
        return predictions

    def generate_pdf_report(self, portfolio: Portfolio, metrics: Dict) -> str:
        """Generate PDF report with portfolio analysis"""
        filename = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("Portfolio Analysis Report", styles["Title"]))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))

        # Portfolio Metrics
        elements.append(Paragraph("Portfolio Metrics", styles["Heading1"]))
        metrics_data = [
            ["Metric", "Value"],
            ["Total Value", f"${metrics['total_value']:,.2f}"],
            ["Daily P&L", f"${metrics['daily_pl']:,.2f}"],
            ["VaR (95%)", f"${metrics['var_95']:,.2f}"],
            ["Volatility", f"{metrics['volatility']*100:.2f}%"],
            ["Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}"],
            ["Beta", f"{metrics['beta']:.2f}"]
        ]
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(metrics_table)

        # Positions Table
        elements.append(Paragraph("Portfolio Positions", styles["Heading1"]))
        positions_data = [["Ticker", "Shares", "Purchase Price", "Current Price", "Market Value", "Unrealized P&L", "Weight"]]
        for pos in portfolio.positions:
            positions_data.append([
                pos.ticker,
                f"{pos.shares:,.0f}",
                f"${pos.purchase_price:.2f}",
                f"${pos.current_price:.2f}",
                f"${pos.market_value:,.2f}",
                f"${pos.unrealized_pl:,.2f}",
                f"{pos.weight*100:.2f}%"
            ])
        positions_table = Table(positions_data)
        positions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(positions_table)

        # LASSO Predictions
        elements.append(Paragraph("Next Day Return Predictions (LASSO)", styles["Heading1"]))
        predictions_data = [["Ticker", "Predicted Return"]]
        for ticker, pred in metrics["lasso_predictions"].items():
            predictions_data.append([ticker, f"{pred*100:.2f}%"])
        predictions_table = Table(predictions_data)
        predictions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(predictions_table)

        doc.build(elements)
        return filename
