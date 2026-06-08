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
print(f"DEBUG: BOT_TOKEN = {BOT_TOKEN[:10] if BOT_TOKEN else 'NOT_SET'}...")

# ============================================
# ПОДДЕРЖКА ЯЗЫКОВ
# ============================================

BOT_TEXTS = {
    "ru": {
        "welcome_unlinked": "🤖 <b>Crypto IS Bot</b>\n\nДобро пожаловать! Чтобы пользоваться ботом, привяжите аккаунт.\n\n<b>🔗 Как привязать:</b>\n1. Войдите в личный кабинет на сайте\n2. Перейдите во вкладку \"Telegram\"\n3. Скопируйте 6-значный код\n4. Отправьте его сюда\n\n🌐 <a href='https://cryptois.abrdns.com'>Перейти на сайт</a>",
        "welcome_linked": "🤖 <b>Crypto IS Bot</b>\n\nС возвращением, {{username}}!\n\n<b>📋 Основные команды:</b>\n/price — BTC и ETH\n/top — топ-5 криптовалют\n/stocks — популярные акции\n/crypto — список всех криптовалют\n/stocks_full — список всех акций\n/crypto_info BTC — детали по крипте\n/stock_info AAPL — детали по акции\n/news — последние новости\n/fear — индекс страха и жадности\n/help — все команды\n\n<b>👤 Аккаунт:</b>\n/status — статус привязки\n/unlink — отвязать",
        "help_linked": "📋 <b>Все команды:</b>\n\n<b>💰 Цены:</b>\n/price — BTC и ETH\n/top — топ-5 криптовалют\n/stocks — популярные акции\n/crypto_info BTC — детальная информация по крипте\n/stock_info AAPL — детальная информация по акции\n/fear — индекс страха и жадности\n\n<b>📋 Списки:</b>\n/crypto — все криптовалюты\n/stocks_full — все акции\n\n<b>📰 Новости:</b>\n/news — последние новости\n\n<b>👤 Аккаунт:</b>\n/status — статус привязки\n/unlink — отвязать",
        "help_unlinked": "📋 <b>Доступные команды:</b>\n\n/start — приветствие\n/help — этот список\n\n🔒 Для доступа к остальным командам привяжите аккаунт.\nОтправьте 6-значный код из личного кабинета.",
        "need_auth": "🔒 <b>Доступ ограничен</b>\n\nВы не привязали свой Telegram к аккаунту Crypto IS.\n\n<b>Как привязать:</b>\n1. Войдите в личный кабинет на сайте\n2. Перейдите во вкладку \"Telegram\"\n3. Скопируйте код и отправьте его сюда\n\n🌐 <a href='https://cryptois.abrdns.com'>Перейти на сайт</a>",
        "price_title": "💰 <b>Текущие цены</b>",
        "btc": "₿ Bitcoin (BTC)",
        "eth": "💎 Ethereum (ETH)",
        "price_usd": "Цена: <b>${:,.0f}</b>",
        "price_change": "24ч: {} {:.2f}%",
        "top_title": "🏆 <b>Топ-5 криптовалют</b>",
        "stocks_title": "📈 <b>Популярные акции</b>",
        "news_title": "📰 <b>Последние новости</b>",
        "fear_title": "😨 <b>Индекс страха и жадности</b>",
        "no_data": "❌ Не удалось получить данные.",
        "no_news": "❌ Не удалось загрузить новости.",
        "need_crypto_symbol": "❌ Укажите тикер: /crypto_info BTC",
        "need_stock_symbol": "❌ Укажите тикер: /stock_info AAPL",
        "unknown": "❓ Неизвестная команда. /help",
        "linked_status": "✅ Аккаунт привязан к <b>{}</b>",
        "not_linked_status": "❌ Аккаунт не привязан.",
        "unlinked": "✅ Аккаунт отвязан.",
        "login_notification": "🔐 <b>Вход в систему</b>\n\n👤 {}\n🌐 {}\n🕐 {}",
        "invalid_code": "❌ Неверный код",
        "code_sent": "✅ Код подтверждён",
    },
    "en": {
        "welcome_unlinked": "🤖 <b>Crypto IS Bot</b>\n\nWelcome! To use the bot, link your account.\n\n<b>🔗 How to link:</b>\n1. Log in to your account on the website\n2. Go to the \"Telegram\" tab\n3. Copy the 6-digit code\n4. Send it here\n\n🌐 <a href='https://cryptois.abrdns.com'>Go to website</a>",
        "welcome_linked": "🤖 <b>Crypto IS Bot</b>\n\nWelcome back, {{username}}!\n\n<b>📋 Main commands:</b>\n/price — BTC and ETH\n/top — top-5 cryptocurrencies\n/stocks — popular stocks\n/crypto — all cryptocurrencies\n/stocks_full — all stocks\n/crypto_info BTC — crypto details\n/stock_info AAPL — stock details\n/news — latest news\n/fear — Fear & Greed Index\n/help — all commands\n\n<b>👤 Account:</b>\n/status — link status\n/unlink — unlink",
        "help_linked": "📋 <b>All commands:</b>\n\n<b>💰 Prices:</b>\n/price — BTC and ETH\n/top — top-5 cryptocurrencies\n/stocks — popular stocks\n/crypto_info BTC — detailed crypto info\n/stock_info AAPL — detailed stock info\n/fear — Fear & Greed Index\n\n<b>📋 Lists:</b>\n/crypto — all cryptocurrencies\n/stocks_full — all stocks\n\n<b>📰 News:</b>\n/news — latest news\n\n<b>👤 Account:</b>\n/status — link status\n/unlink — unlink",
        "help_unlinked": "📋 <b>Available commands:</b>\n\n/start — welcome\n/help — this list\n\n🔒 To access other commands, link your account.\nSend the 6-digit code from your profile.",
        "need_auth": "🔒 <b>Access restricted</b>\n\nYou haven't linked your Telegram to your Crypto IS account.\n\n<b>How to link:</b>\n1. Log in to your account on the website\n2. Go to the \"Telegram\" tab\n3. Copy the 6-digit code and send it here\n\n🌐 <a href='https://cryptois.abrdns.com'>Go to website</a>",
        "price_title": "💰 <b>Current prices</b>",
        "btc": "₿ Bitcoin (BTC)",
        "eth": "💎 Ethereum (ETH)",
        "price_usd": "Price: <b>${:,.0f}</b>",
        "price_change": "24h: {} {:.2f}%",
        "top_title": "🏆 <b>Top-5 cryptocurrencies</b>",
        "stocks_title": "📈 <b>Popular stocks</b>",
        "news_title": "📰 <b>Latest news</b>",
        "fear_title": "😨 <b>Fear & Greed Index</b>",
        "no_data": "❌ Failed to get data.",
        "no_news": "❌ Failed to load news.",
        "need_crypto_symbol": "❌ Specify ticker: /crypto_info BTC",
        "need_stock_symbol": "❌ Specify ticker: /stock_info AAPL",
        "unknown": "❓ Unknown command. /help",
        "linked_status": "✅ Account linked to <b>{}</b>",
        "not_linked_status": "❌ Account not linked.",
        "unlinked": "✅ Account unlinked.",
        "login_notification": "🔐 <b>Login to system</b>\n\n👤 {}\n🌐 {}\n🕐 {}",
        "invalid_code": "❌ Invalid code",
        "code_sent": "✅ Code confirmed",
    },
    "zh": {
        "welcome_unlinked": "🤖 <b>Crypto IS 机器人</b>\n\n欢迎！要使用机器人，请先绑定您的账户。\n\n<b>🔗 如何绑定：</b>\n1. 登录网站账户\n2. 进入“Telegram”选项卡\n3. 复制6位验证码\n4. 发送到这里\n\n🌐 <a href='https://cryptois.abrdns.com'>访问网站</a>",
        "welcome_linked": "🤖 <b>Crypto IS 机器人</b>\n\n欢迎回来，{{username}}！\n\n<b>📋 主要命令：</b>\n/price — 比特币和以太坊\n/top — 加密货币前五名\n/stocks — 热门股票\n/crypto — 所有加密货币\n/stocks_full — 所有股票\n/crypto_info BTC — 加密货币详细信息\n/stock_info AAPL — 股票详细信息\n/news — 最新新闻\n/fear — 恐惧与贪婪指数\n/help — 所有命令\n\n<b>👤 账户：</b>\n/status — 绑定状态\n/unlink — 解绑",
        "help_linked": "📋 <b>所有命令：</b>\n\n<b>💰 价格：</b>\n/price — 比特币和以太坊\n/top — 加密货币前五名\n/stocks — 热门股票\n/crypto_info BTC — 加密货币详细信息\n/stock_info AAPL — 股票详细信息\n/fear — 恐惧与贪婪指数\n\n<b>📋 列表：</b>\n/crypto — 所有加密货币\n/stocks_full — 所有股票\n\n<b>📰 新闻：</b>\n/news — 最新新闻\n\n<b>👤 账户：</b>\n/status — 绑定状态\n/unlink — 解绑",
        "help_unlinked": "📋 <b>可用命令：</b>\n\n/start — 欢迎\n/help — 此列表\n\n🔒 要访问其他命令，请绑定您的账户。\n发送个人资料中的6位验证码。",
        "need_auth": "🔒 <b>访问受限</b>\n\n您尚未将 Telegram 绑定到 Crypto IS 账户。\n\n<b>如何绑定：</b>\n1. 登录网站账户\n2. 进入“Telegram”选项卡\n3. 复制6位验证码并发送到这里\n\n🌐 <a href='https://cryptois.abrdns.com'>访问网站</a>",
        "price_title": "💰 <b>当前价格</b>",
        "btc": "₿ 比特币 (BTC)",
        "eth": "💎 以太坊 (ETH)",
        "price_usd": "价格：<b>${:,.0f}</b>",
        "price_change": "24小时：{} {:.2f}%",
        "top_title": "🏆 <b>加密货币前五名</b>",
        "stocks_title": "📈 <b>热门股票</b>",
        "news_title": "📰 <b>最新新闻</b>",
        "fear_title": "😨 <b>恐惧与贪婪指数</b>",
        "no_data": "❌ 无法获取数据。",
        "no_news": "❌ 无法加载新闻。",
        "need_crypto_symbol": "❌ 请指定代币：/crypto_info BTC",
        "need_stock_symbol": "❌ 请指定代码：/stock_info AAPL",
        "unknown": "❓ 未知命令。发送 /help",
        "linked_status": "✅ 账户已绑定到 <b>{}</b>",
        "not_linked_status": "❌ 账户未绑定。",
        "unlinked": "✅ 账户已解绑。",
        "login_notification": "🔐 <b>系统登录</b>\n\n👤 {}\n🌐 {}\n🕐 {}",
        "invalid_code": "❌ 验证码错误",
        "code_sent": "✅ 验证码已验证",
    }
}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_user_language(chat_id: str) -> str:
    """Получает язык пользователя из базы данных"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Проверяем, есть ли колонка language
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'language' in columns:
            cursor.execute("""
                SELECT language FROM users 
                WHERE telegram_chat_id = ? AND telegram_verified = 1
            """, (chat_id,))
            result = cursor.fetchone()
            if result and result["language"]:
                return result["language"]
    except Exception as e:
        print(f"Ошибка получения языка: {e}")
    return "ru"  # язык по умолчанию

def send_localized_message(chat_id: str, key: str, **kwargs) -> bool:
    """Отправляет локализованное сообщение"""
    if not BOT_TOKEN or not chat_id:
        return False
    
    lang = get_user_language(chat_id)
    text = BOT_TEXTS.get(lang, BOT_TEXTS["ru"]).get(key, key)
    
    # Подставляем параметры
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace("{{" + k + "}}", str(v))
            text = text.replace("{" + k + "}", str(v))
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

# Оставляем старую функцию для обратной совместимости
def send_telegram_message(chat_id: str, message: str) -> bool:
    """Отправляет сырое сообщение в Telegram"""
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
        send_localized_message(chat_id, "need_auth")
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
            send_localized_message(chat_id, "welcome_linked", username=user['username'])
        else:
            send_localized_message(chat_id, "welcome_unlinked")

    elif command == "/help":
        if is_user_verified(chat_id):
            send_localized_message(chat_id, "help_linked")
        else:
            send_localized_message(chat_id, "help_unlinked")

    elif command == "/price":
        data = get_crypto_prices()
        if data:
            btc, eth = data.get("bitcoin", {}), data.get("ethereum", {})
            btc_emoji = "🟢" if btc.get("usd_24h_change", 0) >= 0 else "🔴"
            eth_emoji = "🟢" if eth.get("usd_24h_change", 0) >= 0 else "🔴"
            
            lang = get_user_language(chat_id)
            texts = BOT_TEXTS.get(lang, BOT_TEXTS["ru"])
            
            message = f"""
{texts['price_title']}

<b>{texts['btc']}</b>
{texts['price_usd'].format(btc.get('usd', 0))}
{texts['price_change'].format(btc_emoji, btc.get('usd_24h_change', 0))}

<b>{texts['eth']}</b>
{texts['price_usd'].format(eth.get('usd', 0))}
{texts['price_change'].format(eth_emoji, eth.get('usd_24h_change', 0))}
"""
            send_telegram_message(chat_id, message)
        else:
            send_localized_message(chat_id, "no_data")

    elif command == "/top":
        data = get_top_cryptos()
        if data:
            lang = get_user_language(chat_id)
            texts = BOT_TEXTS.get(lang, BOT_TEXTS["ru"])
            lines = [f"{texts['top_title']}\n"]
            for i, coin in enumerate(data, 1):
                emoji = "🟢" if coin["price_change_percentage_24h"] >= 0 else "🔴"
                lines.append(f"{i}. <b>{coin['name']} ({coin['symbol'].upper()})</b>")
                lines.append(f"   ${coin['current_price']:,.2f} {emoji} {coin['price_change_percentage_24h']:+.2f}%")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_localized_message(chat_id, "no_data")

    elif command == "/stocks":
        data = get_stocks_prices()
        if data:
            lang = get_user_language(chat_id)
            texts = BOT_TEXTS.get(lang, BOT_TEXTS["ru"])
            lines = [f"{texts['stocks_title']}\n"]
            for sym, info in data.items():
                emoji = "🟢" if info["change"] >= 0 else "🔴"
                lines.append(f"<b>{info['name']} ({sym})</b>")
                lines.append(f"   ${info['price']:,.2f} {emoji} {info['change']:+.2f}%")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_localized_message(chat_id, "no_data")

    elif command == "/news":
        news = get_latest_news()
        if news:
            lang = get_user_language(chat_id)
            texts = BOT_TEXTS.get(lang, BOT_TEXTS["ru"])
            lines = [f"{texts['news_title']}\n"]
            for i, entry in enumerate(news, 1):
                title = entry.title[:80] + "..." if len(entry.title) > 80 else entry.title
                lines.append(f"{i}. <a href='{entry.link}'>{title}</a>\n")
            send_telegram_message(chat_id, "\n".join(lines))
        else:
            send_localized_message(chat_id, "no_news")

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
            lang = get_user_language(chat_id)
            texts = BOT_TEXTS.get(lang, BOT_TEXTS["ru"])
            send_telegram_message(chat_id, f"{texts['fear_title']}\n\n{emoji} <b>{value}</b> — {classification}")
        else:
            send_localized_message(chat_id, "no_data")

    elif command == "/crypto_info":
        if len(parts) < 2:
            send_localized_message(chat_id, "need_crypto_symbol")
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
            send_localized_message(chat_id, "no_crypto_data", symbol=symbol)
            send_telegram_message(chat_id, f"❌ Не удалось найти данные для {symbol}.")

    elif command == "/stock_info":
        if len(parts) < 2:
            send_localized_message(chat_id, "need_stock_symbol")
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
            send_localized_message(chat_id, "no_stock_data", symbol=symbol)
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
            send_localized_message(chat_id, "linked_status", username=user['username'])
        else:
            send_localized_message(chat_id, "not_linked_status")

    elif command == "/unlink":
        unlink_telegram(chat_id)
        send_localized_message(chat_id, "unlinked")

    # ===== КОД ПРИВЯЗКИ (6 ЦИФР) =====
    elif len(text) == 6 and text.isdigit():
        success, message = verify_telegram(chat_id, text)
        if success:
            send_localized_message(chat_id, "code_sent")
        else:
            send_localized_message(chat_id, "invalid_code")

    # ===== НЕИЗВЕСТНАЯ КОМАНДА =====
    else:
        send_localized_message(chat_id, "unknown")

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
        send_localized_message(chat_id, "login_notification", username=username, ip=ip, time=datetime.now().strftime('%H:%M:%S'))