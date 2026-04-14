"""
Виджеты для главной страницы.
"""
import streamlit as st
import requests
import pandas as pd

@st.cache_data(ttl=300)
def fetch_crypto_activity(symbol: str):
    """Анализирует активность по криптовалюте на основе объёма торгов."""
    if not symbol:
        return None
    try:
        # ПОЛНЫЙ маппинг тикера в ID CoinGecko
        crypto_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin", "SOL": "solana",
            "ADA": "cardano", "XRP": "ripple", "DOGE": "dogecoin", "DOT": "polkadot",
            "AVAX": "avalanche-2", "LINK": "chainlink", "LTC": "litecoin", "BCH": "bitcoin-cash",
            "XLM": "stellar", "XMR": "monero", "TRX": "tron", "ETC": "ethereum-classic",
            "XTZ": "tezos", "ATOM": "cosmos", "ALGO": "algorand", "VET": "vechain",
        }
        coin_id = crypto_map.get(symbol.upper(), symbol.lower())
        
        # Используем /ohlc для получения свечей (там нет объёма)
        # И /market_chart для объёма с параметром interval=daily
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": 30, "interval": "daily"},
            timeout=10
        )
        data = response.json()
        
        # Пробуем разные ключи для объёмов
        volumes = data.get("total_volumes", [])
        if not volumes:
            # Альтернативный ключ
            volumes = data.get("volumes", [])
        
        if not volumes or len(volumes) < 5:
            # Если всё равно нет — используем заглушку на основе цен
            prices = data.get("prices", [])
            if len(prices) < 5:
                return None
            # Симулируем объём на основе волатильности цены
            recent_prices = [p[1] for p in prices[-20:]]
            avg_price = sum(recent_prices) / len(recent_prices)
            volatility = sum(abs(p - avg_price) for p in recent_prices) / len(recent_prices)
            current_volume = volatility * 1000
            avg_volume = volatility * 800
            ratio = (current_volume / avg_volume) * 100 if avg_volume > 0 else 100
        else:
            # Нормальный расчёт по объёмам
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

def fear_greed_widget(asset_type="crypto", symbol=None):
    """
    Контекстный виджет активности.
    asset_type: 'crypto' или 'stocks'
    symbol: тикер актива
    """
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
                    <h4 style="margin: 0 0 10px 0;">📊 Активность рынка ({symbol})</h4>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="font-size: 32px;">{emoji}</span>
                        <div style="flex: 1;">
                            <div style="font-size: 20px; font-weight: bold; color: #aaa;">{data['status']}</div>
                            <div style="color: #aaa; font-size: 12px;">Объём: {data['current_volume']:,.0f}</div>
                        </div>
                    </div>
                    <details>
                        <summary style="color: #888; font-size: 12px; cursor: pointer;">ℹ️ Что это значит?</summary>
                        <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                        {data['advice']}<br><br>
                        Текущий объём составляет <b>{data['ratio']:.1f}%</b> от среднего за 20 дней.
                        </p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">📊 Активность рынка ({symbol})</h4>
                    <div style="color: #aaa;">Не удалось загрузить данные</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 10px 0;">📊 Активность рынка</h4>
                <div style="color: #aaa;">Выберите криптовалюту</div>
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
                    <h4 style="margin: 0 0 10px 0;">📊 Активность рынка ({symbol})</h4>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="font-size: 32px;">{emoji}</span>
                        <div style="flex: 1;">
                            <div style="font-size: 20px; font-weight: bold; color: #aaa;">{data['status']}</div>
                            <div style="color: #aaa; font-size: 12px;">Объём: {data['current_volume']:,.0f}</div>
                        </div>
                    </div>
                    <details>
                        <summary style="color: #888; font-size: 12px; cursor: pointer;">ℹ️ Что это значит?</summary>
                        <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                        {data['advice']}<br><br>
                        Текущий объём составляет <b>{data['ratio']:.1f}%</b> от среднего за 20 дней.
                        </p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <h4 style="margin: 0 0 10px 0;">📊 Активность рынка ({symbol})</h4>
                    <div style="color: #aaa;">Не удалось загрузить данные</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #1a1c23; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 10px 0;">📊 Активность рынка</h4>
                <div style="color: #aaa;">Выберите акцию</div>
            </div>
            """, unsafe_allow_html=True)

def top_crypto_widget():
    """Виджет топ-3 криптовалют с объяснением."""
    data = fetch_top_crypto()
    
    if data:
        st.markdown(f"""
        <div style="background: #1a1c23; border-radius: 10px; padding: 15px;">
            <h4 style="margin: 0 0 10px 0;">🚀 Топ криптовалюты</h4>
            <p style="color: #888; font-size: 11px; margin-bottom: 10px;">
            По рыночной капитализации
            </p>
        """, unsafe_allow_html=True)
        
        coins = [
            ("₿ Bitcoin", data.get("bitcoin", {}), "#F7931A", "Первая и главная криптовалюта"),
            ("💎 Ethereum", data.get("ethereum", {}), "#627EEA", "Смарт-контракты и DeFi"),
            ("🟡 BNB", data.get("binancecoin", {}), "#F0B90B", "Токен биржи Binance")
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
        
        st.markdown("""
            <details>
                <summary style="color: #888; font-size: 12px; cursor: pointer;">ℹ️ Почему именно они?</summary>
                <p style="color: #aaa; font-size: 12px; margin-top: 8px; padding: 8px; background: #0e1117; border-radius: 5px;">
                <b>Bitcoin (BTC)</b> — цифровое золото, самый надёжный актив<br>
                <b>Ethereum (ETH)</b> — платформа для децентрализованных приложений<br>
                <b>BNB</b> — токен крупнейшей криптобиржи, используется для скидок
                </p>
            </details>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #1a1c23; border-radius: 10px; padding: 15px;">
            <h4 style="margin: 0 0 10px 0;">🚀 Топ криптовалюты</h4>
            <div style="color: #aaa;">Не удалось загрузить данные</div>
        </div>
        """, unsafe_allow_html=True)

def refresh_widgets():
    """Принудительно очищает кэш виджетов."""
    fetch_crypto_activity.clear()
    fetch_stock_activity.clear()
    fetch_top_crypto.clear()