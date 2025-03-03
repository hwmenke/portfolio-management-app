from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Position(BaseModel):
    ticker: str
    shares: float
    purchase_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pl: Optional[float] = None
    weight: Optional[float] = None

class Portfolio(BaseModel):
    positions: List[Position]
    total_value: Optional[float] = None
    daily_pl: Optional[float] = None
    var_95: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    beta: Optional[float] = None
    last_updated: Optional[datetime] = None
