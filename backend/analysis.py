import numpy as np
import pandas as pd
from typing import Dict, List
import json
from datetime import datetime

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

        # Calculate basic metrics without heavy statistical libraries
        returns = self._calculate_returns(portfolio)
        
        metrics = {
            "total_value": total_value,
            "daily_pl": self._calculate_daily_pl(returns),
            "var_95": self._calculate_var(returns),
            "volatility": self._calculate_volatility(returns),
            "sharpe_ratio": self._calculate_sharpe_ratio(returns),
            "beta": self._calculate_simple_beta(returns)
        }

        return metrics

    def _calculate_returns(self, portfolio: Portfolio) -> List[float]:
        """Calculate simple returns for the portfolio"""
        # In a real application, you would fetch historical data
        # For now, return sample data
        return [0.001, -0.002, 0.003, -0.001, 0.002]  # Sample returns

    def _calculate_daily_pl(self, returns: List[float]) -> float:
        """Calculate daily P&L"""
        if returns:
            return returns[-1]
        return 0.0

    def _calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk using historical simulation"""
        if returns:
            sorted_returns = sorted(returns)
            index = int((1 - confidence_level) * len(returns))
            return sorted_returns[index]
        return 0.0

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if returns:
            return np.std(returns) * np.sqrt(252)  # Annualize daily volatility
        return 0.0

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if returns:
            excess_returns = [r - self.risk_free_rate/252 for r in returns]
            if len(excess_returns) > 0:
                return np.sqrt(252) * np.mean(excess_returns) / np.std(returns)
        return 0.0

    def _calculate_simple_beta(self, returns: List[float]) -> float:
        """Calculate a simplified beta"""
        # In a real application, you would compare against market returns
        return 1.0  # Simplified beta calculation

    def generate_json_report(self, portfolio: Portfolio, metrics: Dict) -> Dict:
        """Generate a JSON report instead of PDF"""
        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio": {
                "total_value": metrics["total_value"],
                "metrics": metrics,
                "positions": [
                    {
                        "ticker": pos.ticker,
                        "shares": pos.shares,
                        "current_price": pos.current_price,
                        "market_value": pos.market_value,
                        "weight": pos.weight
                    }
                    for pos in portfolio.positions
                ]
            }
        }
