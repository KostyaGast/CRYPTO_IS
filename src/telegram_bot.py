"""
Модуль Telegram бота с полным набором команд.
Доступ только для привязанных пользователей.
"""
import requests
import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ЗАЩИТА ОТ ПОВТОРНОГО ЗАПУСКА
if os.environ.get("TELEGRAM_POLLING_RUNNING") == "1":
    print("⚠️ Polling уже запущен, выходим")
    sys.exit(0)
os.environ["TELEGRAM_POLLING_RUNNING"] = "1"

# Правильный путь к .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import (
    verify_telegram, get_telegram_chat_id, get_user_by_id,
    get_connection
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
print(f"DEBUG: BOT_TOKEN = {BOT_TOKEN[:10]}...")

# ============================================
# ПРОВЕРКА ПРИВЯЗКИ
# ============================================

def is_user_verified(chat_id: str) -> bool:
    """Проверяет, привязан ли пользователь к аккаунту."""
    user = get_user_by_chat_id(chat_id)
    return user is not None

def require_auth(chat_id: str) -> bool:
    """Требует авторизацию. Возвращает True, если пользователь привязан."""
    if not is_user_verified(chat_id):
        send_telegram_message(chat_id, """
🔒 <b>Доступ ограничен</b>

Вы не привязали свой Telegram к аккаунту Crypto IS.

<b>Как привязать:</b>
1. Войдите в личный кабинет на сайте
2. Перейдите во вкладку "Telegram"
3. Скопируйте код и отправьте его сюда

🌐 <a href="https://cryptois.abrdns.com">Перейти на сайт</a>
""")
        return False
    return True

# ============================================
# БАЗОВЫЕ ФУНКЦИИ
# ============================================

def unlink_telegram(chat_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET telegram_chat_id = NULL, telegram_verified = 0 WHERE telegram_chat_id = ?",
        (chat_id,)
    )
    conn.commit()
    conn.close()
    return True

def send_telegram_message(chat_id: str, message: str) -> bool:
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def get_user_by_chat_id(chat_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username FROM users WHERE telegram_chat_id = ? AND telegram_verified = 1",
        (chat_id,)
    )
    user = cursor.fetchone()
    conn.close()
    return user

# ============================================
# API ЗАПРОСЫ - ОБЩИЕ
# ============================================

def get_crypto_prices():
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10
        )
        return response.json()
    except:
        return None

def get_fear_greed():
    try:
        response = requests.get("https://api.alternative.me/fng/", timeout=10)
        return response.json()["data"][0]
    except:
        return None

def get_top_cryptos():
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 5, "page": 1},
            timeout=10
        )
        return response.json()
    except:
        return None

def get_stocks_prices():
    try:
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        names = {"AAPL": "Apple", "GOOGL": "Google", "MSFT": "Microsoft", "AMZN": "Amazon", "TSLA": "Tesla"}
        prices = {}
        for sym in symbols:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            meta = data['chart']['result'][0]['meta']
            price = meta['regularMarketPrice']
            prev_close = meta['previousClose']
            change = ((price - prev_close) / prev_close) * 100
            prices[sym] = {"name": names[sym], "price": price, "change": change}
        return prices
    except Exception as e:
        print(f"Ошибка получения акций: {e}")
        return None

def get_latest_news():
    try:
        import feedparser
        feed = feedparser.parse("https://cointelegraph.com/rss")
        return feed.entries[:3]
    except:
        return None

def get_all_cryptos():
    return [
        "BTC - Bitcoin", "ETH - Ethereum", "BNB - Binance Coin", "SOL - Solana",
        "ADA - Cardano", "XRP - Ripple", "DOGE - Dogecoin", "DOT - Polkadot",
        "AVAX - Avalanche", "LINK - Chainlink", "LTC - Litecoin", "BCH - Bitcoin Cash",
        "XLM - Stellar", "XMR - Monero", "TRX - Tron", "ETC - Ethereum Classic",
        "XTZ - Tezos", "ATOM - Cosmos", "ALGO - Algorand", "VET - VeChain",
    ]

def get_all_stocks():
    return [
        "AAPL - Apple", "GOOGL - Google", "MSFT - Microsoft", "AMZN - Amazon",
        "TSLA - Tesla", "NVDA - NVIDIA", "META - Meta", "NFLX - Netflix",
        "AMD - AMD", "INTC - Intel", "ADBE - Adobe", "CRM - Salesforce",
        "PYPL - PayPal", "SHOP - Shopify", "ZM - Zoom", "SPOT - Spotify",
        "TWTR - Twitter/X", "SNAP - Snapchat", "UBER - Uber", "ABNB - Airbnb",
        "COIN - Coinbase", "HOOD - Robinhood", "PLTR - Palantir",
        "^GSPC - S&P 500", "^IXIC - Nasdaq", "^DJI - Dow Jones",
    ]

# ============================================
# API ЗАПРОСЫ - ДЕТАЛЬНАЯ ИНФОРМАЦИЯ
# ============================================

def get_crypto_info(symbol: str):
    try:
        crypto_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin", "SOL": "solana",
            "ADA": "cardano", "XRP": "ripple", "DOGE": "dogecoin", "DOT": "polkadot",
            "AVAX": "avalanche-2", "LINK": "chainlink", "LTC": "litecoin", "BCH": "bitcoin-cash",
            "XLM": "stellar", "XMR": "monero", "TRX": "tron", "ETC": "ethereum-classic",
            "XTZ": "tezos", "ATOM": "cosmos", "ALGO": "algorand", "VET": "vechain"
        }
        coin_id = crypto_map.get(symbol.upper())
        if not coin_id:
            return None
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}",
            params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"},
            timeout=10
        )
        data = response.json()
        market_data = data.get("market_data", {})
        current = market_data.get("current_price", {}).get("usd", 0)
        high_24h = market_data.get("high_24h", {}).get("usd", 0)
        low_24h = market_data.get("low_24h", {}).get("usd", 0)
        change_24h = market_data.get("price_change_percentage_24h", 0)
        avg_24h = (high_24h + low_24h) / 2 if high_24h and low_24h else current
        return {
            "name": data.get("name", symbol),
            "symbol": symbol.upper(),
            "current": current,
            "high": high_24h,
            "low": low_24h,
            "avg": avg_24h,
            "change": change_24h
        }
    except:
        return None

def get_stock_info(symbol: str):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        meta = data["chart"]["result"][0]["meta"]
        current = meta.get("regularMarketPrice", 0)
        high_24h = meta.get("regularMarketDayHigh", 0)
        low_24h = meta.get("regularMarketDayLow", 0)
        prev = meta.get("previousClose", current)
        change = ((current - prev) / prev) * 100 if prev else 0
        avg_24h = (high_24h + low_24h) / 2 if high_24h and low_24h else current
        return {
            "name": meta.get("longName", symbol),
            "symbol": symbol.upper(),
            "current": current,
            "high": high_24h,
            "low": low_24h,
            "avg": avg_24h,
            "change": change
        }
    except:
        return None

# ============================================
# ОБРАБОТЧИК КОМАНД (С ПРОВЕРКОЙ ПРИВЯЗКИ)
# ============================================

def process_telegram_update(update: dict):
    message = update.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()
    
    if not chat_id or not text:
        return
    
    print(f"📱 Получено сообщение от {chat_id}: {text}")
    parts = text.split()
    command = parts[0].lower() if parts else ""

    # ===== ПРОВЕРКА ПРИВЯЗКИ (кроме кода и /start) =====
    is_six_digit_code = len(text) == 6 and text.isdigit()
    
    if not is_six_digit_code and command not in ["/start", "/help"]:
        if not require_auth(chat_id):
            return

    # ===== КОМАНДЫ =====
    
    if command == "/start":
        if is_user_verified(chat_id):
            user = get_user_by_chat_id(chat_id)
            send_telegram_message(chat_id, f"""
🤖 <b>Crypto IS Bot</b>

С возвращением, {user['username']}!

<b>📋 Основные команды:</b>
/price — BTC и ETH
/top — топ-5 криптовалют
/stocks — популярные акции
/crypto — список всех криптовалют
/stocks_full — список всех акций
/crypto_info BTC — детали по крипте
/stock_info AAPL — детали по акции
/news — последние новости
/fear — индекс страха и жадности
/help — все команды

<b>👤 Аккаунт:</b>
/status — статус привязки
/unlink — отвязать
""")
        else:
            send_telegram_message(chat_id, """
🤖 <b>Crypto IS Bot</b>

Добро пожаловать! Чтобы пользоваться ботом, привяжите аккаунт.

<b>🔗 Как привязать:</b>
1. Войдите в личный кабинет на сайте
2. Перейдите во вкладку "Telegram"
3. Скопируйте 6-значный код
4. Отправьте его сюда

🌐 <a href="https://cryptois.abrdns.com">Перейти на сайт</a>
""")

    elif command == "/help":
        if is_user_verified(chat_id):
            send_telegram_message(chat_id, """
📋 <b>Все команды:</b>

<b>💰 Цены:</b>
/price — BTC и ETH
/top — топ-5 криптовалют
/stocks — популярные акции
/crypto_info BTC — детальная информация по крипте
/stock_info AAPL — детальная информация по акции
/fear — индекс страха и жадности

<b>📋 Списки:</b>
/crypto — все криптовалюты
/stocks_full — все акции

<b>📰 Новости:</b>
/news — последние новости

<b>👤 Аккаунт:</b>
/status — статус привязки
/unlink — отвязать
""")
        else:
            send_telegram_message(chat_id, """
📋 <b>Доступные команды:</b>

/start — приветствие
/help — этот список

🔒 Для доступа к остальным командам привяжите аккаунт.
Отправьте 6-значный код из личного кабинета.
""")

    elif command == "/price":
        data = get_crypto_prices()
        if data:
            btc, eth = data.get("bitcoin", {}), data.get("ethereum", {})
            btc_emoji = "🟢" if btc.get("usd_24h_change", 0) >= 0 else "🔴"
            eth_emoji = "🟢" if eth.get("usd_24h_change", 0) >= 0 else "🔴"
            message = f"""
💰 <b>Текущие цены</b>

<b>₿ Bitcoin (BTC)</b>
Цена: <b>${btc.get('usd', 0):,.0f}</b>
24ч: {btc_emoji} {btc.get('usd_24h_change', 0):+.2f}%

<b>💎 Ethereum (ETH)</b>
Цена: <b>${eth.get('usd', 0):,.0f}</b>
24ч: {eth_emoji} {eth.get('usd_24h_change', 0):+.2f}%
"""
            send_telegram_message(chat_id, message)
        else:
            send_telegram_message(chat_id, "❌ Не удалось получить данные.")

    elif command == "/top":
        data = get_top_cryptos()
        if data:
            lines = ["🏆 <b>Топ-5 криптовалют</b>\n"]
            for i, coin in enumerate(data, 1):
                emoji = "🟢" if coin["price_change_percentage_24h"] >= 0 else "🔴"
                lines.append(f"{i}. <b>{coin['name']} ({coin['symbol'].upper()})</b>")
                lines.append(f"   ${coin['current_price']:,.2f} {emoji} {coin['price_change_percentage_24h']:+.2f}%")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_telegram_message(chat_id, "❌ Не удалось получить данные.")

    elif command == "/stocks":
        data = get_stocks_prices()
        if data:
            lines = ["📈 <b>Популярные акции</b>\n"]
            for sym, info in data.items():
                emoji = "🟢" if info["change"] >= 0 else "🔴"
                lines.append(f"<b>{info['name']} ({sym})</b>")
                lines.append(f"   ${info['price']:,.2f} {emoji} {info['change']:+.2f}%")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_telegram_message(chat_id, "❌ Не удалось получить данные.")

    elif command == "/news":
        news = get_latest_news()
        if news:
            lines = ["📰 <b>Последние новости</b>\n"]
            for i, entry in enumerate(news, 1):
                title = entry.title[:80] + "..." if len(entry.title) > 80 else entry.title
                lines.append(f"{i}. <a href='{entry.link}'>{title}</a>\n")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_telegram_message(chat_id, "❌ Не удалось загрузить новости.")

    elif command == "/fear":
        data = get_fear_greed()
        if data:
            value = int(data["value"])
            classification = data["value_classification"]
            if value < 25: emoji = "😱"
            elif value < 45: emoji = "😰"
            elif value < 55: emoji = "😐"
            elif value < 75: emoji = "😊"
            else: emoji = "🤑"
            send_telegram_message(chat_id, f"😨 <b>Индекс страха и жадности</b>\n\n{emoji} <b>{value}</b> — {classification}")
        else:
            send_telegram_message(chat_id, "❌ Не удалось получить данные.")

    elif command == "/crypto_info":
        if len(parts) < 2:
            send_telegram_message(chat_id, "❌ Укажите тикер: /crypto_info BTC")
            return
        symbol = parts[1].upper()
        data = get_crypto_info(symbol)
        if data:
            emoji = "🟢" if data["change"] >= 0 else "🔴"
            message = f"""
🪙 <b>{data['name']} ({data['symbol']})</b>

💰 Текущая: <b>${data['current']:,.2f}</b>
📊 Максимум (24ч): <b>${data['high']:,.2f}</b>
📉 Минимум (24ч): <b>${data['low']:,.2f}</b>
📈 Средняя (24ч): <b>${data['avg']:,.2f}</b>
24ч изменение: {emoji} {data['change']:+.2f}%

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            send_telegram_message(chat_id, message)
        else:
            send_telegram_message(chat_id, f"❌ Не удалось найти данные для {symbol}.")

    elif command == "/stock_info":
        if len(parts) < 2:
            send_telegram_message(chat_id, "❌ Укажите тикер: /stock_info AAPL")
            return
        symbol = parts[1].upper()
        data = get_stock_info(symbol)
        if data:
            emoji = "🟢" if data["change"] >= 0 else "🔴"
            message = f"""
📈 <b>{data['name']} ({data['symbol']})</b>

💰 Текущая: <b>${data['current']:,.2f}</b>
📊 Максимум (24ч): <b>${data['high']:,.2f}</b>
📉 Минимум (24ч): <b>${data['low']:,.2f}</b>
📈 Средняя (24ч): <b>${data['avg']:,.2f}</b>
24ч изменение: {emoji} {data['change']:+.2f}%

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            send_telegram_message(chat_id, message)
        else:
            send_telegram_message(chat_id, f"❌ Не удалось найти данные для {symbol}.")

    elif command == "/crypto":
        cryptos = get_all_cryptos()
        lines = ["🪙 <b>Доступные криптовалюты</b>\n"]
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        start, end = (page - 1) * 10, page * 10
        for i, c in enumerate(cryptos[start:end], start + 1):
            lines.append(f"{i}. {c}")
        total = (len(cryptos) + 9) // 10
        if page < total:
            lines.append(f"\n📄 {page}/{total} | /crypto {page + 1}")
        send_telegram_message(chat_id, "\n".join(lines))

    elif command == "/stocks_full":
        stocks = get_all_stocks()
        lines = ["📈 <b>Доступные акции</b>\n"]
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        start, end = (page - 1) * 10, page * 10
        for i, s in enumerate(stocks[start:end], start + 1):
            lines.append(f"{i}. {s}")
        total = (len(stocks) + 9) // 10
        if page < total:
            lines.append(f"\n📄 {page}/{total} | /stocks_full {page + 1}")
        send_telegram_message(chat_id, "\n".join(lines))

    elif command == "/status":
        user = get_user_by_chat_id(chat_id)
        if user:
            send_telegram_message(chat_id, f"✅ Аккаунт привязан к <b>{user['username']}</b>")
        else:
            send_telegram_message(chat_id, "❌ Аккаунт не привязан.")

    elif command == "/unlink":
        unlink_telegram(chat_id)
        send_telegram_message(chat_id, "✅ Аккаунт отвязан.")

    # ===== КОД ПРИВЯЗКИ (6 ЦИФР) =====
    elif len(text) == 6 and text.isdigit():
        success, message = verify_telegram(chat_id, text)
        send_telegram_message(chat_id, message)

    # ===== НЕИЗВЕСТНАЯ КОМАНДА =====
    else:
        send_telegram_message(chat_id, "❓ Неизвестная команда. /help")

# ============================================
# POLLING
# ============================================

def start_polling():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не настроен")
        return
    print("✅ Бот слушает...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            data = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35).json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    process_telegram_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            time.sleep(5)

def init_bot():
    if BOT_TOKEN:
        threading.Thread(target=start_polling, daemon=True).start()
        print("✅ Бот запущен в фоне")
    else:
        print("❌ Бот не настроен")

def send_login_notification(user_id: int, username: str, ip: str):
    chat_id = get_telegram_chat_id(user_id)
    if chat_id:
        send_telegram_message(chat_id, f"🔐 <b>Вход в систему</b>\n\n👤 {username}\n🌐 {ip}\n🕐 {datetime.now().strftime('%H:%M:%S')}")