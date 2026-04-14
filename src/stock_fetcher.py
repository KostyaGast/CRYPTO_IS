"""
Модуль получения данных по акциям через Yahoo Finance.
"""
import pandas as pd
import yfinance as yf
from typing import Dict

# Мировые акции
WORLD_STOCKS = {
    "🌍 Apple (AAPL)": "AAPL",
    "🌍 Google (GOOGL)": "GOOGL",
    "🌍 Microsoft (MSFT)": "MSFT",
    "🌍 Amazon (AMZN)": "AMZN",
    "🌍 Tesla (TSLA)": "TSLA",
    "🌍 NVIDIA (NVDA)": "NVDA",
    "🌍 Meta (META)": "META",
    "🌍 Netflix (NFLX)": "NFLX",
    "🌍 AMD (AMD)": "AMD",
    "🌍 Intel (INTC)": "INTC",
    "🌍 Adobe (ADBE)": "ADBE",
    "🌍 Salesforce (CRM)": "CRM",
    "🌍 PayPal (PYPL)": "PYPL",
    "🌍 Shopify (SHOP)": "SHOP",
    "🌍 Zoom (ZM)": "ZM",
    "🌍 Spotify (SPOT)": "SPOT",
    "🌍 Twitter/X (TWTR)": "TWTR",
    "🌍 Snapchat (SNAP)": "SNAP",
    "🌍 Uber (UBER)": "UBER",
    "🌍 Airbnb (ABNB)": "ABNB",
    "🌍 Coinbase (COIN)": "COIN",
    "🌍 Robinhood (HOOD)": "HOOD",
    "🌍 Palantir (PLTR)": "PLTR",
    "🌍 S&P 500 (^GSPC)": "^GSPC",
    "🌍 Nasdaq (^IXIC)": "^IXIC",
    "🌍 Dow Jones (^DJI)": "^DJI",
}

POPULAR_STOCKS = WORLD_STOCKS.copy()


class StockFetcher:
    """Класс для получения данных по акциям."""
    
    def __init__(self, symbol: str = "AAPL", period: str = "1mo"):
        self.symbol = symbol
        self.period = period
        
    def get_data(self) -> pd.DataFrame:
        """Получение исторических данных."""
        ticker = yf.Ticker(self.symbol)
        df = ticker.history(period=self.period)
        
        if df.empty:
            return pd.DataFrame()
        
        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.dropna()
        
        return df
    
    def get_info(self) -> Dict:
        """Получение информации о компании."""
        ticker = yf.Ticker(self.symbol)
        info = ticker.info
        
        return {
            "name": info.get("longName", self.symbol),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "previous_close": info.get("regularMarketPreviousClose", 0),
            "currency": info.get("currency", "USD"),
        }