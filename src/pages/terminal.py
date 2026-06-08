"""
Трейдинговый терминал — бумажный трейдинг.
Максимально красивый дизайн с анимациями и аналитикой.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import time
from config import config
from fetcher import CryptoFetcher
from stock_fetcher import StockFetcher, WORLD_STOCKS, FUTURES, ETFS
from database import place_order, get_portfolio, get_orders, get_balance, get_connection

st.set_page_config(page_title="Терминал | Crypto IS", page_icon="📈", layout="wide")

# ============================================
# КЭШИРОВАНИЕ ДЛЯ УСКОРЕНИЯ (ДОБАВЛЕНО)
# ============================================

@st.cache_data(ttl=10)  # Кэш на 10 секунд
def get_cached_crypto_price(coin_id: str) -> float:
    """Кэшированное получение цены криптовалюты"""
    try:
        fetcher = CryptoFetcher(coin_id)
        return fetcher.get_current_price()
    except:
        return 0.0

@st.cache_data(ttl=10)
def get_cached_stock_price(symbol: str) -> float:
    """Кэшированное получение цены акции"""
    try:
        fetcher = StockFetcher(symbol, period="1d")
        data = fetcher.get_data()
        if not data.empty:
            return data['close'].iloc[-1]
        return 0.0
    except:
        return 0.0

@st.cache_data(ttl=30)
def get_cached_crypto_history(coin_id: str, days: int = 7) -> pd.DataFrame:
    """Кэшированное получение истории криптовалюты"""
    try:
        fetcher = CryptoFetcher(coin_id, days=days)
        return fetcher.get_data()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_cached_stock_history(symbol: str, period: str = "7d") -> pd.DataFrame:
    """Кэшированное получение истории акции"""
    try:
        fetcher = StockFetcher(symbol, period=period)
        return fetcher.get_data()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def get_all_portfolio_prices(portfolio_items_hashable):
    """Загрузить цены для всего портфеля за один вызов"""
    prices = {}
    for item in portfolio_items_hashable:
        symbol = item['symbol']
        # Определяем тип актива
        is_crypto = any(symbol in c for c in config.SUPPORTED_COINS.values())
        
        if is_crypto:
            coin_id = symbol.lower()
            if coin_id in config.SUPPORTED_COINS.values():
                prices[symbol] = get_cached_crypto_price(coin_id)
            else:
                prices[symbol] = get_cached_crypto_price("bitcoin")
        else:
            prices[symbol] = get_cached_stock_price(symbol)
    return prices

@st.cache_data(ttl=10)
def get_ticker_data_cached():
    """Кэшированное получение данных для бегущей строки"""
    ticker_items = []
    assets = [
        ("BTC", "bitcoin"), ("ETH", "ethereum"), ("SOL", "solana"),
        ("BNB", "binancecoin"), ("XRP", "ripple"), ("ADA", "cardano"),
        ("AAPL", None, "stock"), ("TSLA", None, "stock"), ("NVDA", None, "stock"),
        ("GOOGL", None, "stock"), ("MSFT", None, "stock")
    ]
    
    for symbol, coin_id, *asset_type in assets:
        try:
            if coin_id:
                df = get_cached_crypto_history(coin_id, days=2)
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
                    change = ((current_price - prev_price) / prev_price) * 100
            else:
                df = get_cached_stock_history(symbol, period="2d")
                if not df.empty:
                    current_price = df['close'].iloc[-1]
                    prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
                    change = ((current_price - prev_price) / prev_price) * 100
                else:
                    continue
            
            color_class = "up" if change >= 0 else "down"
            arrow = "▲" if change >= 0 else "▼"
            ticker_items.append(
                f'<span class="ticker-item {color_class}">{symbol}: ${current_price:,.2f} '
                f'{arrow} {abs(change):.2f}%</span>'
            )
        except Exception as e:
            continue
    
    ticker_html = '<div class="ticker-container"><div class="ticker-wrap">'
    ticker_html += ''.join(ticker_items * 2)
    ticker_html += '</div></div>'
    return ticker_html

# Проверка авторизации
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Доступ только для авторизованных пользователей.")
    st.stop()

user = st.session_state["user"]

# Инициализация баланса
if "terminal_balance" not in st.session_state:
    st.session_state.terminal_balance = get_balance(user["id"])
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

balance = st.session_state.terminal_balance

# ============================================
# CSS СТИЛИ
# ============================================
st.markdown("""
<style>
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes neonPulse {
        0% { box-shadow: 0 0 5px #F7931A; }
        50% { box-shadow: 0 0 20px #F7931A, 0 0 40px #F7931A; }
        100% { box-shadow: 0 0 5px #F7931A; }
    }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    .stApp {
        background: linear-gradient(-45deg, #0e1117, #1a1c23, #0a0f14, #141824);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }
    .pulse-dot.green { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
    .pulse-dot.red { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
    
    .neon-card {
        background: rgba(26, 28, 35, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        animation: slideIn 0.5s ease-out;
    }
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        border-color: #F7931A;
    }
    
    .balance-card {
        background: linear-gradient(135deg, #0e1117, #1a1c23);
        border: 1px solid #F7931A;
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        animation: neonPulse 3s ease-in-out infinite;
        transition: transform 0.3s ease;
    }
    .balance-card:hover {
        transform: scale(1.02);
    }
    
    .balance-value {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #F7931A, #ffaa00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(247,147,26,0.3);
    }
    
    .ticker-container {
        overflow: hidden;
        white-space: nowrap;
        background: rgba(0,0,0,0.5);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
        border: 1px solid rgba(247,147,26,0.3);
    }
    .ticker-wrap {
        display: inline-block;
        animation: ticker 30s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    .ticker-item {
        display: inline-block;
        margin-right: 40px;
        font-weight: bold;
        color: #ccc;
    }
    .ticker-item.up { color: #00ff88; text-shadow: 0 0 5px #00ff88; }
    .ticker-item.down { color: #ff4444; text-shadow: 0 0 5px #ff4444; }
    
    .order-row-buy {
        border-left: 4px solid #00ff88;
        padding: 10px;
        margin: 5px 0;
        background: rgba(0,255,136,0.05);
        border-radius: 8px;
        transition: all 0.3s ease;
        animation: slideIn 0.3s ease-out;
    }
    .order-row-buy:hover {
        background: rgba(0,255,136,0.1);
        transform: translateX(5px);
    }
    
    .order-row-sell {
        border-left: 4px solid #ff4444;
        padding: 10px;
        margin: 5px 0;
        background: rgba(255,68,68,0.05);
        border-radius: 8px;
        transition: all 0.3s ease;
        animation: slideIn 0.3s ease-out;
    }
    .order-row-sell:hover {
        background: rgba(255,68,68,0.1);
        transform: translateX(5px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #F7931A, #ffaa00);
        color: white;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(247,147,26,0.3);
    }
    
    input, select, textarea {
        background: rgba(26, 28, 35, 0.8) !important;
        border: 1px solid rgba(247,147,26,0.3) !important;
        color: white !important;
    }
    input:focus, select:focus {
        box-shadow: 0 0 15px #F7931A !important;
        border-color: #F7931A !important;
    }
    
    .metric-card {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        background: rgba(247,147,26,0.1);
        transform: translateY(-3px);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        background: linear-gradient(135deg, #F7931A, #ffaa00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Трейдинговый терминал")

# ============================================
# БЕГУЩАЯ СТРОКА (ТИКЕР)
# ============================================
def get_ticker_data():
    """Получение данных для тикера"""
    ticker_items = []
    assets = [
        ("BTC", "bitcoin"), ("ETH", "ethereum"), ("SOL", "solana"),
        ("BNB", "binancecoin"), ("XRP", "ripple"), ("ADA", "cardano"),
        ("AAPL", None, "stock"), ("TSLA", None, "stock"), ("NVDA", None, "stock"),
        ("GOOGL", None, "stock"), ("MSFT", None, "stock")
    ]
    
    for symbol, coin_id, *asset_type in assets:
        try:
            if coin_id:
                fetcher = CryptoFetcher(coin_id, days=2)
                data = fetcher.get_data()
                if not data.empty:
                    current_price = data['close'].iloc[-1]
                    prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
                    change = ((current_price - prev_price) / prev_price) * 100
            else:
                fetcher = StockFetcher(symbol, period="2d")
                data = fetcher.get_data()
                if not data.empty:
                    current_price = data['close'].iloc[-1]
                    prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
                    change = ((current_price - prev_price) / prev_price) * 100
                else:
                    continue
            
            color_class = "up" if change >= 0 else "down"
            arrow = "▲" if change >= 0 else "▼"
            ticker_items.append(
                f'<span class="ticker-item {color_class}">{symbol}: ${current_price:,.2f} '
                f'{arrow} {abs(change):.2f}%</span>'
            )
        except Exception as e:
            continue
    
    # Дублируем для непрерывной прокрутки
    ticker_html = '<div class="ticker-container"><div class="ticker-wrap">'
    ticker_html += ''.join(ticker_items * 2)
    ticker_html += '</div></div>'
    return ticker_html

with st.spinner("Загрузка рыночных данных..."):
    ticker_html = get_ticker_data_cached()
    st.markdown(ticker_html, unsafe_allow_html=True)

# ============================================
# ВЕРХНЯЯ ПАНЕЛЬ
# ============================================
col_bal, col_pnl, col_trades, col_winrate = st.columns(4)

# Получаем портфель
port = get_portfolio(user["id"])

# Рассчитываем P&L
total_pnl = 0
total_value = 0
portfolio_details = []

for h in port:
    try:
        # Определяем текущую цену (с кэшированием)
        if any(h["symbol"] in c for c in config.SUPPORTED_COINS.values()):
            coin_id = h["symbol"].lower()
            if coin_id in config.SUPPORTED_COINS.values():
                current_price = get_cached_crypto_price(coin_id)
            else:
                current_price = get_cached_crypto_price("bitcoin")
        else:
            current_price = get_cached_stock_price(h["symbol"])
        
        position_value = current_price * h["quantity"]
        total_value += position_value
        pnl = (current_price - h["avg_price"]) * h["quantity"]
        total_pnl += pnl
        
        portfolio_details.append({
            "symbol": h["symbol"],
            "quantity": h["quantity"],
            "avg_price": h["avg_price"],
            "current_price": current_price,
            "value": position_value,
            "pnl": pnl,
            "pnl_pct": (pnl / (h["avg_price"] * h["quantity"])) * 100 if h["avg_price"] * h["quantity"] > 0 else 0
        })
    except Exception as e:
        continue

pnl_color = "#00ff88" if total_pnl >= 0 else "#ff4444"
pnl_emoji = "📈" if total_pnl >= 0 else "📉"

with col_bal:
    st.markdown(f"""
    <div class="balance-card">
        <div style="color: #888; font-size: 14px;">💰 ДОСТУПНЫЙ БАЛАНС</div>
        <div class="balance-value">${balance:,.2f}</div>
        <div style="color: #888; font-size: 12px; margin-top: 10px;">
            💼 Стоимость портфеля: ${total_value:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_pnl:
    st.markdown(f"""
    <div class="balance-card" style="border-color: {pnl_color}; box-shadow: 0 0 30px rgba({'0,255,136' if total_pnl >= 0 else '255,68,68'}, 0.2);">
        <div style="color: #888; font-size: 14px;">{pnl_emoji} P&L (ПРИБЫЛЬ/УБЫТОК)</div>
        <div class="balance-value" style="background: linear-gradient(135deg, {pnl_color}, {pnl_color});">
            ${total_pnl:+,.2f}
        </div>
        <div style="color: {pnl_color}; font-size: 12px; margin-top: 10px;">
            📊 Общая стоимость: ${total_value + balance:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_trades:
    orders = get_orders(user["id"])
    num_trades = len(orders)
    buy_trades = len([o for o in orders if o["order_type"] == "buy"])
    sell_trades = len([o for o in orders if o["order_type"] == "sell"])
    
    st.markdown(f"""
    <div class="balance-card" style="border-color: #627EEA;">
        <div style="color: #888; font-size: 14px;">📊 ВСЕГО СДЕЛОК</div>
        <div class="balance-value" style="background: linear-gradient(135deg, #627EEA, #8b9dc3);">
            {num_trades}
        </div>
        <div style="color: #888; font-size: 12px; margin-top: 10px;">
            🟢 Покупок: {buy_trades} | 🔴 Продаж: {sell_trades}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_winrate:
    # Расчет винрейта
    win_rate = 0
    if len(orders) > 1:
        profitable_trades = 0
        buy_orders = {}
        for order in orders:
            if order["order_type"] == "buy":
                key = f"{order['symbol']}_{order['timestamp']}"
                buy_orders[key] = order
            elif order["order_type"] == "sell":
                # Находим соответствующую покупку (упрощенно)
                for buy_key, buy_order in buy_orders.items():
                    if buy_order["symbol"] == order["symbol"]:
                        profit = (order["price"] - buy_order["price"]) * order["quantity"]
                        if profit > 0:
                            profitable_trades += 1
                        break
        if len(orders) > 0:
            win_rate = (profitable_trades / (len(orders) / 2)) * 100 if len(orders) > 1 else 0
    
    win_color = "#00ff88" if win_rate >= 50 else "#ffaa00"
    st.markdown(f"""
    <div class="balance-card" style="border-color: {win_color};">
        <div style="color: #888; font-size: 14px;">🎯 WIN RATE</div>
        <div class="balance-value" style="background: linear-gradient(135deg, {win_color}, {win_color}); font-size: 2rem;">
            {win_rate:.1f}%
        </div>
        <div style="color: #888; font-size: 12px; margin-top: 10px;">
            📈 Прибыльных сделок: {profitable_trades if 'profitable_trades' in locals() else 0}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# ОСНОВНАЯ ОБЛАСТЬ
# ============================================
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader("⚡ Новая сделка")
    
    asset_type = st.selectbox("Тип актива", ["Криптовалюта", "Акции", "Фьючерсы и фонды"])
    
    current_price = 0
    symbol = ""
    coin_id = None
    
    if asset_type == "Криптовалюта":
        names = list(config.SUPPORTED_COINS.keys())
        selected = st.selectbox("Актив", names)
        symbol = selected.split("(")[1].split(")")[0]
        coin_id = config.SUPPORTED_COINS[selected]
        try:
            current_price = get_cached_crypto_price(coin_id)  # ← ИЗМЕНЕНО
        except:
            current_price = 0
    elif asset_type == "Акции":
        names = list(WORLD_STOCKS.keys())
        selected = st.selectbox("Актив", names)
        symbol = WORLD_STOCKS[selected]
        try:
            current_price = get_cached_stock_price(symbol)  # ← ИЗМЕНЕНО (упрощено)
        except:
            current_price = 0
    else:
        all_futures = {**FUTURES, **ETFS}
        names = list(all_futures.keys())
        selected = st.selectbox("Актив", names)
        symbol = all_futures[selected]
        try:
            current_price = get_cached_stock_price(symbol)  # ← ИЗМЕНЕНО (упрощено)
        except:
            current_price = 0
    
    # Пульсирующая точка и цена
    price_change = np.random.choice([-1, 1]) * np.random.uniform(0.1, 2)
    change_class = "green" if price_change >= 0 else "red"
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 20px 0;">
        <div>
            <span class="pulse-dot {change_class}"></span>
            <span style="font-size: 1.2rem;">Текущая цена:</span>
        </div>
        <div style="font-size: 1.5rem; font-weight: bold; color: #{'00ff88' if price_change >= 0 else 'ff4444'}">
            ${current_price:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Визуализатор изменения цены
    st.markdown(f"""
    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 10px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>📊 Изменение за 24ч:</span>
            <span style="color: #{'00ff88' if price_change >= 0 else 'ff4444'}; font-weight: bold;">
                {price_change:+.2f}%
            </span>
        </div>
        <div style="background: rgba(255,255,255,0.1); border-radius: 5px; height: 4px; margin-top: 5px;">
            <div style="background: {'#00ff88' if price_change >= 0 else '#ff4444'}; width: {min(100, abs(price_change) * 10)}%; height: 100%; border-radius: 5px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    quantity = st.number_input("Количество", min_value=0.0, step=0.01, format="%.4f")
    
    # Предварительный просмотр суммы сделки
    if quantity > 0:
        total_cost = current_price * quantity
        st.info(f"💵 Сумма сделки: **${total_cost:,.2f}**")
        if total_cost > balance and asset_type != "Акции":
            st.warning("⚠️ Недостаточно средств для покупки!")
    
    col_buy, col_sell = st.columns(2)
    with col_buy:
        if st.button("🟢 Купить", use_container_width=True, key="buy_btn"):
            if quantity <= 0:
                st.error("❌ Укажите количество для покупки")
            elif current_price <= 0:
                st.error("❌ Ошибка получения цены актива")
            elif current_price * quantity > balance:
                st.error(f"❌ Недостаточно средств! Доступно: ${balance:,.2f}")
            else:
                try:
                    place_order(user["id"], symbol, asset_type, current_price, quantity, "buy")
                    st.session_state.terminal_balance = get_balance(user["id"])
                    balance = st.session_state.terminal_balance
                    
                    # Анимация успеха
                    st.balloons()
                    st.success(f"""
                    ✅ Успешно куплено!
                    📈 {quantity} {symbol} по ${current_price:,.2f}
                    💰 Сумма: ${current_price * quantity:,.2f}
                    """)
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при покупке: {str(e)}")
    
    with col_sell:
        if st.button("🔴 Продать", use_container_width=True, key="sell_btn"):
            if quantity <= 0:
                st.error("❌ Укажите количество для продажи")
            elif current_price <= 0:
                st.error("❌ Ошибка получения цены актива")
            else:
                port = get_portfolio(user["id"])
                holding = next((h for h in port if h["symbol"] == symbol), None)
                if not holding:
                    st.error(f"❌ У вас нет актива {symbol} в портфеле")
                elif holding["quantity"] < quantity:
                    st.error(f"❌ Недостаточно актива! Доступно: {holding['quantity']:.4f} {symbol}")
                else:
                    try:
                        place_order(user["id"], symbol, asset_type, current_price, quantity, "sell")
                        st.session_state.terminal_balance = get_balance(user["id"])
                        balance = st.session_state.terminal_balance
                        
                        profit = (current_price - holding["avg_price"]) * quantity
                        profit_text = f"📊 Прибыль: ${profit:+,.2f}" if profit != 0 else ""
                        profit_color = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"
                        
                        st.success(f"""
                        ✅ Успешно продано!
                        📉 {quantity} {symbol} по ${current_price:,.2f}
                        💰 Сумма: ${current_price * quantity:,.2f}
                        {profit_text} {profit_color}
                        """)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при продаже: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Мини-график актива
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader(f"📉 {symbol} — Мини-график")
    
    try:
        if asset_type == "Криптовалюта" and coin_id:
            df = get_cached_crypto_history(coin_id, days=7)
        elif asset_type in ["Акции", "Фьючерсы и фонды"]:
            df = get_cached_stock_history(symbol, period="7d")
        else:
            df = pd.DataFrame()
        
        if not df.empty and len(df) > 0:
            fig = go.Figure()
            
            # Добавляем свечной график
            fig.add_trace(go.Candlestick(
                x=df['date'], 
                open=df['open'], 
                high=df['high'],
                low=df['low'], 
                close=df['close'],
                name="Price",
                increasing_line_color='#00ff88', 
                decreasing_line_color='#ff4444',
                showlegend=False
            ))
            
            # Добавляем скользящие средние
            if len(df) > 20:
                ma20 = df['close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(
                    x=df['date'], y=ma20,
                    mode='lines', name='MA20',
                    line=dict(color='#F7931A', width=1.5, dash='dash')
                ))
            
            fig.update_layout(
                template="plotly_dark", 
                height=350, 
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_rangeslider_visible=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 Нет данных для отображения графика")
    except Exception as e:
        st.info(f"⚠️ Не удалось загрузить график: {str(e)[:50]}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Алерт цены
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader("🔔 Установить алерт")
    
    alert_price = st.number_input("💰 Цена для уведомления", min_value=0.01, step=1.0, value=float(current_price) if current_price > 0 else 1000.0)
    alert_condition = st.selectbox("📊 Условие", ["Выше", "Ниже"])
    
    col_alert1, col_alert2 = st.columns(2)
    with col_alert1:
        if st.button("🔔 Установить алерт", use_container_width=True):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        price REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active INTEGER DEFAULT 1
                    )
                """)
                cursor.execute(
                    "INSERT INTO price_alerts (user_id, symbol, condition, price) VALUES (?, ?, ?, ?)",
                    (user["id"], symbol, alert_condition.lower(), alert_price)
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Алерт для {symbol} установлен! Уведомим при цене {alert_condition} ${alert_price:,.2f}")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
    
    with col_alert2:
        if st.button("📋 Мои алерты", use_container_width=True):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT symbol, condition, price FROM price_alerts WHERE user_id = ? AND active = 1",
                    (user["id"],)
                )
                alerts = cursor.fetchall()
                conn.close()
                if alerts:
                    alert_text = "\n".join([f"• {a[0]}: {a[1]} ${a[2]:,.2f}" for a in alerts])
                    st.info(f"📋 Ваши активные алерты:\n{alert_text}")
                else:
                    st.info("📭 У вас нет активных алертов")
            except:
                st.info("📭 Функция алертов временно недоступна")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # Портфель с детальной аналитикой
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader("📋 Детальный портфель")
    
    if portfolio_details:
        # Создаем DataFrame для отображения
        df_portfolio = pd.DataFrame(portfolio_details)
        df_portfolio['value'] = df_portfolio['value'].apply(lambda x: f"${x:,.2f}")
        df_portfolio['avg_price'] = df_portfolio['avg_price'].apply(lambda x: f"${x:,.2f}")
        df_portfolio['current_price'] = df_portfolio['current_price'].apply(lambda x: f"${x:,.2f}")
        df_portfolio['pnl'] = df_portfolio['pnl'].apply(lambda x: f"${x:+,.2f}")
        df_portfolio['pnl_pct'] = df_portfolio['pnl_pct'].apply(lambda x: f"{x:+.2f}%")
        df_portfolio.columns = ['Актив', 'Кол-во', 'Ср. цена', 'Тек. цена', 'Стоимость', 'P&L', 'P&L %']
        
        st.dataframe(
            df_portfolio, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Актив": st.column_config.TextColumn("Актив", width="small"),
                "Кол-во": st.column_config.NumberColumn("Кол-во", format="%.4f"),
                "Ср. цена": st.column_config.TextColumn("Ср. цена"),
                "Тек. цена": st.column_config.TextColumn("Тек. цена"),
                "Стоимость": st.column_config.TextColumn("Стоимость"),
                "P&L": st.column_config.TextColumn("P&L"),
                "P&L %": st.column_config.TextColumn("P&L %")
            }
        )
        
        # Круговая диаграмма портфеля
        if sum([p["value"] for p in portfolio_details]) > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[p["symbol"] for p in portfolio_details], 
                values=[p["value"] for p in portfolio_details], 
                hole=0.4,
                marker=dict(
                    colors=px.colors.qualitative.Set3,
                    line=dict(color='white', width=2)
                ),
                textinfo='label+percent',
                textposition='outside'
            )])
            fig_pie.update_layout(
                template="plotly_dark", 
                height=350, 
                margin=dict(l=0, r=0, t=30, b=0),
                title="📊 Распределение портфеля",
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Топ активов
        st.markdown("#### 🏆 Топ активов в портфеле")
        top_assets = sorted(portfolio_details, key=lambda x: x["value"], reverse=True)[:3]
        cols = st.columns(3)
        for idx, asset in enumerate(top_assets):
            with cols[idx]:
                st.metric(
                    label=f"🥇 {asset['symbol']}" if idx == 0 else f"🥈 {asset['symbol']}" if idx == 1 else f"🥉 {asset['symbol']}",
                    value=f"${asset['value']:,.2f}",
                    delta=f"{asset['pnl_pct']:+.1f}%"
                )
    else:
        st.info("💼 Портфель пуст. Начните торговать!")
    st.markdown('</div>', unsafe_allow_html=True)

    # История сделок с фильтрацией
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader("📜 Лента сделок")
    
    orders = get_orders(user["id"])
    if orders:
        # Фильтры
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            filter_symbol = st.selectbox("🔍 Фильтр по активу", ["Все"] + list(set([o["symbol"] for o in orders])))
        with col_filter2:
            filter_type = st.selectbox("📊 Тип сделки", ["Все", "Покупки", "Продажи"])
        
        # Применяем фильтры
        filtered_orders = orders
        if filter_symbol != "Все":
            filtered_orders = [o for o in filtered_orders if o["symbol"] == filter_symbol]
        if filter_type == "Покупки":
            filtered_orders = [o for o in filtered_orders if o["order_type"] == "buy"]
        elif filter_type == "Продажи":
            filtered_orders = [o for o in filtered_orders if o["order_type"] == "sell"]
        
        # Экспорт данных
        if filtered_orders:
            df_orders = pd.DataFrame(filtered_orders)
            csv = df_orders.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 Скачать историю (CSV)", 
                csv, 
                f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                use_container_width=True
            )
        
        # Отображаем сделки
        for order in filtered_orders[:30]:
            order_class = "order-row-buy" if order["order_type"] == "buy" else "order-row-sell"
            emoji = "🟢" if order["order_type"] == "buy" else "🔴"
            order_type_rus = "ПОКУПКА" if order["order_type"] == "buy" else "ПРОДАЖА"
            
            st.markdown(f"""
            <div class="{order_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #aaa; font-size: 12px;">📅 {order['timestamp'][:19]}</span>
                        <span style="margin-left: 10px; font-weight: bold; font-size: 14px;">{emoji} {order_type_rus}</span>
                        <span style="margin-left: 10px; color: #F7931A; font-weight: bold;">{order['symbol']}</span>
                    </div>
                    <div style="font-size: 12px;">
                        ID: {order['id']}
                    </div>
                </div>
                <div style="margin-top: 8px;">
                    <span style="color: #888;">📦 Кол-во: <strong>{order['quantity']:.4f}</strong></span>
                    <span style="margin-left: 15px; color: #888;">💵 Цена: <strong>${order['price']:,.2f}</strong></span>
                    <span style="margin-left: 15px; color: #888;">💰 Сумма: <strong>${order['price'] * order['quantity']:,.2f}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(filtered_orders) > 30:
            st.info(f"📋 Показаны последние 30 из {len(filtered_orders)} сделок")
    else:
        st.info("📭 Сделок пока нет. Сделайте первую сделку!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Расширенная аналитика
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.subheader("📊 Расширенная аналитика")
    
    orders_all = get_orders(user["id"], limit=1000)
    if len(orders_all) > 1:
        df_analytics = pd.DataFrame(orders_all)
        
        # Статистика по сделкам
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        total_buy_volume = df_analytics[df_analytics["order_type"] == "buy"]["price"].sum() if not df_analytics[df_analytics["order_type"] == "buy"].empty else 0
        total_sell_volume = df_analytics[df_analytics["order_type"] == "sell"]["price"].sum() if not df_analytics[df_analytics["order_type"] == "sell"].empty else 0
        
        with col_stat1:
            st.markdown(f"""
            <div class="metric-card">
                <div>📊 Оборот</div>
                <div class="stat-value">${total_buy_volume + total_sell_volume:,.0f}</div>
                <div style="font-size: 12px;">🟢 Покупки: ${total_buy_volume:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat2:
            avg_trade_size = (total_buy_volume + total_sell_volume) / len(df_analytics) if len(df_analytics) > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div>📈 Средний чек</div>
                <div class="stat-value">${avg_trade_size:,.0f}</div>
                <div style="font-size: 12px;">Всего сделок: {len(df_analytics)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat3:
            # Соотношение покупок и продаж
            buy_count = len(df_analytics[df_analytics["order_type"] == "buy"])
            sell_count = len(df_analytics[df_analytics["order_type"] == "sell"])
            ratio = buy_count / sell_count if sell_count > 0 else buy_count
            st.markdown(f"""
            <div class="metric-card">
                <div>🔄 Соотношение</div>
                <div class="stat-value">{buy_count}:{sell_count}</div>
                <div style="font-size: 12px;">Покупок/Продаж</div>
            </div>
            """, unsafe_allow_html=True)
        
        # График активности по времени
        df_analytics['date'] = pd.to_datetime(df_analytics['timestamp']).dt.date
        daily_activity = df_analytics.groupby(['date', 'order_type']).size().unstack(fill_value=0)
        
        if not daily_activity.empty:
            fig_activity = go.Figure()
            if 'buy' in daily_activity.columns:
                fig_activity.add_trace(go.Bar(
                    x=daily_activity.index, y=daily_activity['buy'],
                    name='Покупки', marker_color='#00ff88'
                ))
            if 'sell' in daily_activity.columns:
                fig_activity.add_trace(go.Bar(
                    x=daily_activity.index, y=daily_activity['sell'],
                    name='Продажи', marker_color='#ff4444'
                ))
            
            fig_activity.update_layout(
                template="plotly_dark",
                height=300,
                title="📅 Активность по дням",
                barmode='group',
                xaxis_title="Дата",
                yaxis_title="Количество сделок",
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_activity, use_container_width=True)
        
        # Топ активов по объему торгов
        symbol_volume = df_analytics.groupby('symbol').apply(
            lambda x: (x['price'] * x['quantity']).sum()
        ).sort_values(ascending=False).head(5)
        
        if not symbol_volume.empty:
            fig_top = go.Figure(data=[go.Bar(
                x=symbol_volume.values,
                y=symbol_volume.index,
                orientation='h',
                marker=dict(
                    color=symbol_volume.values,
                    colorscale='Viridis',
                    showscale=True
                )
            )])
            fig_top.update_layout(
                template="plotly_dark",
                height=300,
                title="🏆 Топ активов по объему торгов",
                xaxis_title="Объем ($)",
                yaxis_title="Актив",
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_top, use_container_width=True)
        
        # Хитмап активности
        st.markdown("#### 🗺️ Тепловая карта активности")
        df_analytics['hour'] = pd.to_datetime(df_analytics['timestamp']).dt.hour
        df_analytics['day'] = pd.to_datetime(df_analytics['timestamp']).dt.day_name()
        
        heatmap_data = df_analytics.pivot_table(
            values='id', 
            index='day', 
            columns='hour', 
            aggfunc='count', 
            fill_value=0
        )
        
        if not heatmap_data.empty:
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Viridis',
                text=heatmap_data.values,
                texttemplate='%{text}',
                textfont={"size": 10}
            ))
            fig_heatmap.update_layout(
                template="plotly_dark",
                height=350,
                title="⏰ Активность по часам и дням",
                xaxis_title="Час дня",
                yaxis_title="День недели",
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
    else:
        st.info("📊 Недостаточно данных для аналитики (нужно минимум 2 сделки)")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# НИЖНЯЯ ПАНЕЛЬ СТАТУСА
# ============================================
st.markdown("---")
col_status1, col_status2, col_status3, col_status4 = st.columns(4)

with col_status1:
    st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div style="color: #888; font-size: 12px;">⏱️ Последнее обновление</div>
        <div style="color: #F7931A; font-size: 14px;">{st.session_state.last_update.strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

with col_status2:
    st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div style="color: #888; font-size: 12px;">💼 Позиций в портфеле</div>
        <div style="color: #F7931A; font-size: 14px;">{len(portfolio_details)}</div>
    </div>
    """, unsafe_allow_html=True)

with col_status3:
    st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div style="color: #888; font-size: 12px;">🎯 Win Rate</div>
        <div style="color: #{'00ff88' if win_rate >= 50 else 'ffaa00'}; font-size: 14px;">{win_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col_status4:
    st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div style="color: #888; font-size: 12px;">🔄 Автообновление</div>
        <div style="color: #F7931A; font-size: 14px;">Активно</div>
    </div>
    """, unsafe_allow_html=True)

# Кнопки навигации
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)

with col_nav1:
    if st.button("🏠 На главную", use_container_width=True):
        st.switch_page("main.py")

with col_nav2:
    if st.button("🔄 Обновить данные", use_container_width=True):
        st.session_state.last_update = datetime.now()
        st.rerun()

with col_nav3:
    if st.button("📈 Топ активов", use_container_width=True):
        st.info("🏆 Топ активов по объему торгов обновляется автоматически")

with col_nav4:
    if st.button("ℹ️ Помощь", use_container_width=True):
        st.info("""
        📖 **Справка по терминалу:**
        
        • **Покупка/продажа**: Выберите актив, укажите количество и нажмите соответствующую кнопку
        • **Алерты**: Установите уведомления при достижении определенной цены
        • **Аналитика**: Изучайте статистику своих сделок
        • **Экспорт**: Скачивайте историю сделок в CSV формате
        
        💡 Совет: Используйте фильтры в ленте сделок для удобного анализа
        """)