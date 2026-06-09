"""
Виджеты для главной страницы.
"""
import streamlit as st
import requests
import pandas as pd

# Поддержка языков (передаётся из main.py)
def get_text(key, lang="ru"):
    texts = {
        "ru": {
            "market_activity": "📊 Активность рынка ({})",
            "no_data": "Не удалось загрузить данные",
            "select_asset": "Выберите актив",
            "volume": "Объём: {:,}",
            "what_mean": "ℹ️ Что это значит?",
            "current_volume_pct": "Текущий объём составляет <b>{:.1f}%</b> от среднего за 20 дней.",
            "top_crypto": "🚀 Топ криптовалюты",
            "top_crypto_sub": "По рыночной капитализации",
            "why_these": "ℹ️ Почему именно они?",
            "btc_desc": "цифровое золото, самый надёжный актив",
            "eth_desc": "платформа для децентрализованных приложений",
            "bnb_desc": "токен крупнейшей криптобиржи, используется для скидок",
        },
        "en": {
            "market_activity": "📊 Market Activity ({})",
            "no_data": "Failed to load data",
            "select_asset": "Select asset",
            "volume": "Volume: {:,}",
            "what_mean": "ℹ️ What does it mean?",
            "current_volume_pct": "Current volume is <b>{:.1f}%</b> of the 20-day average.",
            "top_crypto": "🚀 Top Cryptocurrencies",
            "top_crypto_sub": "By market capitalization",
            "why_these": "ℹ️ Why these?",
            "btc_desc": "digital gold, the most reliable asset",
            "eth_desc": "platform for decentralized applications",
            "bnb_desc": "token of the largest crypto exchange, used for discounts",
        },
        "zh": {
            "market_activity": "📊 市场活动 ({})",
            "no_data": "无法加载数据",
            "select_asset": "选择资产",
            "volume": "交易量: {:,}",
            "what_mean": "ℹ️ 这意味着什么？",
            "current_volume_pct": "当前交易量是20天平均值的<b>{:.1f}%</b>。",
            "top_crypto": "🚀 顶级加密货币",
            "top_crypto_sub": "按市值排名",
            "why_these": "ℹ️ 为什么是它们？",
            "btc_desc": "数字黄金，最可靠的资产",
            "eth_desc": "去中心化应用平台",
            "bnb_desc": "最大加密货币交易所的代币，用于折扣",
        }
    }
    return texts.get(lang, texts["ru"]).get(key, key)

@st.cache_data(ttl=300)
def fetch_crypto_activity(symbol: str):
    """Анализирует активность по криптовалюте на основе объёма торгов."""
    if not symbol:
        return None
    try:
        crypto_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin", "SOL": "solana",
            "ADA": "cardano", "XRP": "ripple", "DOGE": "dogecoin", "DOT": "polkadot",
            "AVAX": "avalanche-2", "LINK": "chainlink", "LTC": "litecoin", "BCH": "bitcoin-cash",
            "XLM": "stellar", "XMR": "monero", "TRX": "tron", "ETC": "ethereum-classic",
            "XTZ": "tezos", "ATOM": "cosmos", "ALGO": "algorand", "VET": "vechain",
        }
        coin_id = crypto_map.get(symbol.upper(), symbol.lower())
        
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": 30, "interval": "daily"},
            timeout=10
        )
        data = response.json()
        
        volumes = data.get("total_volumes", [])
        if not volumes:
            volumes = data.get("volumes", [])
        
        if not volumes or len(volumes) < 5:
            prices = data.get("prices", [])
            if len(prices) < 5:
                return None
            recent_prices = [p[1] for p in prices[-20:]]
            avg_price = sum(recent_prices) / len(recent_prices)
            volatility = sum(abs(p - avg_price) for p in recent_prices) / len(recent_prices)
            current_volume = volatility * 1000
            avg_volume = volatility * 800
            ratio = (current_volume / avg_volume) * 100 if avg_volume > 0 else 100
        else:
            recent_volumes = [v[1] for v in volumes[-20:]]
            current_volume = recent_volumes[-1]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            ratio = (current_volume / avg_volume) * 100 if avg_volume > 0 else 100
        
        if ratio > 150:
            status = "🔥 Экстремально высокая"
            advice = "Повышенный интерес, возможны сильные движения."
        elif ratio > 110:
            status = "📈 Выше среднего"
            advice = "Рынок активен, хорошая ликвидность."
        elif ratio > 90:
            status = "⚖️ Средняя"
            advice = "Обычная торговая активность."
        elif ratio > 70:
            status = "📉 Ниже среднего"
            advice = "Интерес к активу снижен."
        else:
            status = "😴 Низкая"
            advice = "Рынок неактивен, возможен застой."
            
        return {
            "current_volume": current_volume,
            "avg_volume": avg_volume,
            "ratio": ratio,
            "status": status,
            "advice": advice
        }
    except Exception as e:
        print(f"Ошибка получения данных по крипте {symbol}: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_stock_activity(symbol: str):
    """Анализирует активность по акции на основе объёма торгов."""
    if not symbol:
        return None
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        
        if hist.empty or len(hist) < 5:
            return None
            
        avg_volume = hist['Volume'].tail(20).mean()
        current_volume = hist['Volume'].iloc[-1]
        
        if avg_volume > 0:
            ratio = (current_volume / avg_volume) * 100
            if ratio > 150:
                status = "🔥 Экстремально высокая"
                advice = "Повышенный интерес, возможны сильные движения."
            elif ratio > 110:
                status = "📈 Выше среднего"
                advice = "Рынок активен, хорошая ликвидность."
            elif ratio > 90:
                status = "⚖️ Средняя"
                advice = "Обычная торговая активность."
            elif ratio > 70:
                status = "📉 Ниже среднего"
                advice = "Интерес к активу снижен."
            else:
                status = "😴 Низкая"
                advice = "Рынок неактивен, возможен застой."
                
            return {
                "current_volume": current_volume,
                "avg_volume": avg_volume,
                "ratio": ratio,
                "status": status,
                "advice": advice
            }
        return None
    except Exception as e:
        print(f"Ошибка получения данных по акции {symbol}: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_top_crypto():
    """Получает топ-3 криптовалют."""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,binancecoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true"
            },
            timeout=5
        )
        return response.json()
    except:
        return None

def fear_greed_widget(asset_type="crypto", symbol=None, lang="ru"):
    """Контекстный виджет активности."""
    t = get_text(lang)
    
    if asset_type == "Криптовалюта" or asset_type == "crypto":
        if symbol:
            data = fetch_crypto_activity(symbol)
            if data:
                if data['ratio'] > 150: emoji = "🔥"
                elif data['ratio'] > 110: emoji = "📈"
                elif data['ratio'] > 90: emoji = "⚖️"
                elif data['ratio'] > 70: emoji = "📉"
                else: emoji = "😴"

                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format(symbol)}</h4>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="font-size: 32px;">{emoji}</span>
                        <div style="flex: 1;">
                            <div style="font-size: 20px; font-weight: bold; color: #aaa;">{data['status']}</div>
                            <div style="color: #aaa; font-size: 12px;">{t['volume'].format(int(data['current_volume']))}</div>
                        </div>
                    </div>
                    <details>
                        <summary style="color: #888; font-size: 12px; cursor: pointer;">{t['what_mean']}</summary>
                        <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                        {data['advice']}<br><br>
                        {t['current_volume_pct'].format(data['ratio'])}
                        </p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format(symbol)}</h4>
                    <div style="color: #aaa;">{t['no_data']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format('')}</h4>
                <div style="color: #aaa;">{t['select_asset']}</div>
            </div>
            """, unsafe_allow_html=True)

    elif asset_type == "Акции" or asset_type == "stocks":
        if symbol:
            data = fetch_stock_activity(symbol)
            if data:
                if data['ratio'] > 150: emoji = "🔥"
                elif data['ratio'] > 110: emoji = "📈"
                elif data['ratio'] > 90: emoji = "⚖️"
                elif data['ratio'] > 70: emoji = "📉"
                else: emoji = "😴"

                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format(symbol)}</h4>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="font-size: 32px;">{emoji}</span>
                        <div style="flex: 1;">
                            <div style="font-size: 20px; font-weight: bold; color: #aaa;">{data['status']}</div>
                            <div style="color: #aaa; font-size: 12px;">{t['volume'].format(int(data['current_volume']))}</div>
                        </div>
                    </div>
                    <details>
                        <summary style="color: #888; font-size: 12px; cursor: pointer;">{t['what_mean']}</summary>
                        <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                        {data['advice']}<br><br>
                        {t['current_volume_pct'].format(data['ratio'])}
                        </p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format(symbol)}</h4>
                    <div style="color: #aaa;">{t['no_data']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 10px 0;">{t['market_activity'].format('')}</h4>
                <div style="color: #aaa;">{t['select_asset']}</div>
            </div>
            """, unsafe_allow_html=True)

def top_crypto_widget(lang="ru"):
    """Виджет топ-3 криптовалют с объяснением."""
    t = get_text(lang)
    data = fetch_top_crypto()
    
    if data:
        st.markdown(f"""
        <div style="background: #1a1c23; border-radius: 10px; padding: 15px;">
            <h4 style="margin: 0 0 10px 0;">{t['top_crypto']}</h4>
            <p style="color: #888; font-size: 11px; margin-bottom: 10px;">
                {t['top_crypto_sub']}
            </p>
        """, unsafe_allow_html=True)
        
        coins = [
            ("₿ Bitcoin", data.get("bitcoin", {}), "#F7931A", t['btc_desc']),
            ("💎 Ethereum", data.get("ethereum", {}), "#627EEA", t['eth_desc']),
            ("🟡 BNB", data.get("binancecoin", {}), "#F0B90B", t['bnb_desc'])
        ]
        
        for name, coin_data, color, description in coins:
            price = coin_data.get("usd", 0)
            change = coin_data.get("usd_24h_change", 0)
            change_color = "#00ff88" if change >= 0 else "#ff4444"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color: {color};" title="{description}">{name}</span>
                <div style="text-align: right;">
                    <span style="font-weight: bold;">${price:,.0f}</span>
                    <span style="color: {change_color}; margin-left: 8px; font-size: 12px;">{change:+.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <details>
                <summary style="color: #888; font-size: 12px; cursor: pointer;">{t['why_these']}</summary>
                <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                <b>Bitcoin (BTC)</b> — {t['btc_desc']}<br>
                <b>Ethereum (ETH)</b> — {t['eth_desc']}<br>
                <b>BNB</b> — {t['bnb_desc']}
                </p>
            </details>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #1a1c23; border-radius: 10px; padding: 15px;">
            <h4 style="margin: 0 0 10px 0;">{t['top_crypto']}</h4>
            <div style="color: #aaa;">{t['no_data']}</div>
        </div>
        """, unsafe_allow_html=True)

def refresh_widgets():
    """Принудительно очищает кэш виджетов."""
    fetch_crypto_activity.clear()
    fetch_stock_activity.clear()
    fetch_top_crypto.clear()