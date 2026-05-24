"""
Загрузчик исторических данных из внешних API в локальную БД.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import time
from database import bulk_save_crypto_history, bulk_save_stock_history

# ============================================
# ЗАГРУЗКА КРИПТОВАЛЮТ
# ============================================

def fetch_crypto_history_from_coingecko(coin_id: str, days: int = 365) -> List[Dict]:
    """
    Загружает историю криптовалюты из CoinGecko API.
    coin_id: 'bitcoin', 'ethereum', и т.д.
    days: за сколько дней (максимум 365)
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        
        result = []
        for i, (ts, price) in enumerate(prices):
            dt = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            
            # OHLC
            prev_price = prices[i-1][1] if i > 0 else price
            
            volume = 0
            if i < len(volumes) and len(volumes[i]) > 1:
                volume = float(volumes[i][1])
            
            result.append({
                'symbol': coin_id,
                'date': dt,
                'open': prev_price,
                'high': price * 1.002,
                'low': price * 0.998,
                'close': price,
                'volume': volume
            })
        
        return result
    except Exception as e:
        print(f"Ошибка загрузки {coin_id}: {e}")
        return []

def load_all_crypto_history(days: int = 365):
    """
    Загружает историю для ВСЕХ криптовалют из config.SUPPORTED_COINS.
    """
    from config import config
    
    print(f"🔄 Загрузка истории криптовалют за {days} дней...")
    
    for name, coin_id in config.SUPPORTED_COINS.items():
        print(f"  Загрузка {name} ({coin_id})...")
        data = fetch_crypto_history_from_coingecko(coin_id, days)
        if data:
            bulk_save_crypto_history(data)
            print(f"    ✅ Сохранено {len(data)} записей")
        else:
            print(f"    ❌ Не удалось загрузить")
        time.sleep(2)  # Пауза между запросами (лимит API)
    
    print("✅ Загрузка криптовалют завершена!")

# ============================================
# ЗАГРУЗКА АКЦИЙ
# ============================================

def fetch_stock_history_from_yahoo(symbol: str, period: str = "1y") -> List[Dict]:
    """
    Загружает историю акции из Yahoo Finance.
    period: '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            return []
        
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        result = []
        for _, row in df.iterrows():
            result.append({
                'symbol': symbol,
                'date': row['Date'],
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
        
        return result
    except Exception as e:
        print(f"Ошибка загрузки {symbol}: {e}")
        return []

def load_all_stock_history():
    """
    Загружает историю для ВСЕХ акций из stock_fetcher.WORLD_STOCKS.
    """
    from stock_fetcher import WORLD_STOCKS
    
    print(f"🔄 Загрузка истории акций за 1 год...")
    
    for name, symbol in WORLD_STOCKS.items():
        if symbol.startswith("^"):  # Пропускаем индексы
            continue
        print(f"  Загрузка {name} ({symbol})...")
        data = fetch_stock_history_from_yahoo(symbol, "1y")
        if data:
            bulk_save_stock_history(data)
            print(f"    ✅ Сохранено {len(data)} записей")
        else:
            print(f"    ❌ Не удалось загрузить")
        time.sleep(1)
    
    print("✅ Загрузка акций завершена!")

# ============================================
# КОНСОЛЬНЫЙ ЗАПУСК
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "crypto":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
            load_all_crypto_history(days)
        elif sys.argv[1] == "stocks":
            load_all_stock_history()
        elif sys.argv[1] == "all":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
            load_all_crypto_history(days)
            load_all_stock_history()
        else:
            print("Использование: python data_loader.py [crypto|stocks|all] [days]")
    else:
        print("Использование: python data_loader.py [crypto|stocks|all] [days]")