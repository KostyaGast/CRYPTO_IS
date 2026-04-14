"""
Конфигурация приложения.
Все секретные данные читаются из переменных окружения.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Настройки приложения."""
    
    # API
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Данные
    SUPPORTED_COINS = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Binance Coin (BNB)": "binancecoin",
        "Solana (SOL)": "solana",
        "Cardano (ADA)": "cardano",
        "XRP (XRP)": "ripple",
        "Dogecoin (DOGE)": "dogecoin",
        "Polkadot (DOT)": "polkadot",
        "Avalanche (AVAX)": "avalanche-2",
        "Chainlink (LINK)": "chainlink",
        "Litecoin (LTC)": "litecoin",
        "Bitcoin Cash (BCH)": "bitcoin-cash",
        "Stellar (XLM)": "stellar",
        "Monero (XMR)": "monero",
        "Tron (TRX)": "tron",
        "Ethereum Classic (ETC)": "ethereum-classic",
        "Tezos (XTZ)": "tezos",
        "Cosmos (ATOM)": "cosmos",
        "Algorand (ALGO)": "algorand",
        "VeChain (VET)": "vechain",
    }
    # Кэш
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)
    
    # Настройки обновления
    UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "60"))
    DAYS_HISTORY = int(os.getenv("DAYS_HISTORY", "30"))
    
    # Только будние дни
    WEEKDAYS_ONLY = True


# Синглтон конфигурации
config = Config()