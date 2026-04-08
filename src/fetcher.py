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
    
    # Разрешённые значения days для /ohlc
    ALLOWED_DAYS = [1, 7, 14, 30, 90, 180, 365]
    
    def __init__(self, coin_id: str = "bitcoin", days: int = 30):
        self.coin_id = coin_id
        # Округляем до ближайшего разрешённого значения
        self.days = self._round_days(days)
        self.cache_file = config.DATA_DIR / f"{coin_id}_coingecko_cache.json"
        self.base_url = "https://api.coingecko.com/api/v3"
    
    def _round_days(self, days: int) -> int:
        """Округление до ближайшего разрешённого значения."""
        if days <= 1:
            return 1
        if days <= 7:
            return 7
        if days <= 14:
            return 14
        if days <= 30:
            return 30
        if days <= 90:
            return 90
        if days <= 180:
            return 180
        return 365
    
    def _fetch_from_api(self) -> List[Dict]:
        """
        Запрос к CoinGecko API /ohlc.
        """
        url = f"{self.base_url}/coins/{self.coin_id}/ohlc"
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
            
            result = []
            for item in data:
                # CoinGecko OHLC: [timestamp, open, high, low, close]
                ts = item[0]
                dt = datetime.fromtimestamp(ts / 1000)
                
                # ФИЛЬТР: только будние дни (ПН-ПТ)
                if config.WEEKDAYS_ONLY and dt.weekday() >= 5:
                    continue
                
                result.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "timestamp": ts,
                    "open": item[1],
                    "high": item[2],
                    "low": item[3],
                    "close": item[4],
                    "volume": 0,
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
                        if datetime.now() - last_update < timedelta(hours=1):
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


def fetch_both_coins(days: int = 30) -> Dict[str, pd.DataFrame]:
    """Получение данных по BTC и ETH одновременно."""
    btc_fetcher = CryptoFetcher("bitcoin", days)
    eth_fetcher = CryptoFetcher("ethereum", days)
    
    return {
        "BTC": btc_fetcher.get_data(),
        "ETH": eth_fetcher.get_data()
    }