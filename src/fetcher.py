"""
Модуль получения данных с CoinGecko API.
Фильтрация: только будние дни (ПН-ПТ).
"""
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import time

from config import config


class CryptoFetcher:
    """
    Класс для получения и кэширования данных криптовалют через CoinGecko.
    """
    
    def __init__(self, coin_id: str = "bitcoin", days: int = 30):
        self.coin_id = coin_id
        self.days = min(days, 365)
        self.cache_file = config.DATA_DIR / f"{coin_id}_cache.json"
        self.base_url = "https://api.coingecko.com/api/v3"
    
    def _fetch_from_api(self) -> List[Dict]:
        """
        Запрос к CoinGecko API /market_chart (возвращает и цены, и объёмы).
        """
        url = f"{self.base_url}/coins/{self.coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": self.days
        }
        headers = {}
        if config.COINGECKO_API_KEY:
            headers["x-cg-pro-api-key"] = config.COINGECKO_API_KEY
        
        print(f"  Запрос к CoinGecko: {self.coin_id}, {self.days} дней...")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 429:
                print("  Ждём 60 секунд (лимит API)...")
                time.sleep(60)
                response = requests.get(url, params=params, headers=headers, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            # market_chart возвращает: prices, market_caps, total_volumes
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])
            
            result = []
            for i, (ts, price) in enumerate(prices):
                dt = datetime.fromtimestamp(ts / 1000)
                
                # ФИЛЬТР: только будние дни (ПН-ПТ)
                if config.WEEKDAYS_ONLY and dt.weekday() >= 5:
                    continue
                
                # Объём
                volume = 0
                if i < len(volumes) and len(volumes[i]) > 1:
                    try:
                        volume = float(volumes[i][1])
                    except:
                        volume = 0
                
                # Эмулируем OHLC из цен
                prev_price = prices[i-1][1] if i > 0 else price
                
                result.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "timestamp": ts,
                    "open": prev_price,
                    "high": price * 1.002,
                    "low": price * 0.998,
                    "close": price,
                    "volume": volume,
                    "market_cap": 0
                })
            
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"  HTTP Error: {e}")
            return []
        except Exception as e:
            print(f"  Ошибка: {e}")
            return []
    
    def _load_from_cache(self) -> Optional[List[Dict]]:
        """Загрузка данных из кэша."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    if cache.get("days") == self.days:
                        last_update = datetime.fromisoformat(cache.get("updated_at", "2000-01-01"))
                        if datetime.now() - last_update < timedelta(hours=4):
                            return cache.get("data", [])
            except:
                pass
        return None
    
    def _save_to_cache(self, data: List[Dict]) -> None:
        """Сохранение данных в кэш."""
        cache = {
            "updated_at": datetime.now().isoformat(),
            "coin_id": self.coin_id,
            "days": self.days,
            "data": data
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    
    def get_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """Получение данных в виде pandas DataFrame."""
        data = None
        
        if not force_refresh:
            data = self._load_from_cache()
            if data:
                print(f"  Данные загружены из кэша ({len(data)} записей)")
        
        if data is None:
            data = self._fetch_from_api()
            if data:
                self._save_to_cache(data)
                print(f"  Получено {len(data)} записей")
            else:
                data = []
        
        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
        
        return df
    def get_current_price(self) -> float:
        """Получает текущую цену через простой запрос."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": self.coin_id, "vs_currencies": "usd"}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get(self.coin_id, {}).get("usd", 0))
        except:
            pass
        
        # Запасной вариант — из кэша
        df = self.get_data()
        if not df.empty:
            return float(df["close"].iloc[-1])
        
        return 0.0

def fetch_both_coins(days: int = 30) -> Dict[str, pd.DataFrame]:
    """Получение данных по BTC и ETH одновременно."""
    btc_fetcher = CryptoFetcher("bitcoin", days)
    eth_fetcher = CryptoFetcher("ethereum", days)
    
    return {
        "BTC": btc_fetcher.get_data(),
        "ETH": eth_fetcher.get_data()
    }