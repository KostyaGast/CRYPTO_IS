"""
Страница новостей криптовалют.
"""
import streamlit as st
import requests
import feedparser
from datetime import datetime

st.set_page_config(
    page_title="Новости | Crypto IS",
    page_icon="📰",
    layout="wide"
)

# ============================================
# ПРОВЕРКА АВТОРИЗАЦИИ
# ============================================
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Доступ только для авторизованных пользователей.")
    st.stop()

st.title("📰 Новости криптовалют")

# Выбор источника
source = st.selectbox(
    "📡 Источник",
    ["CoinDesk", "Cointelegraph", "Decrypt"]
)

# RSS-ленты
rss_feeds = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed"
}

@st.cache_data(ttl=600)
def fetch_news(feed_url):
    """Загружает новости из RSS."""
    feed = feedparser.parse(feed_url)
    return feed.entries[:15]

with st.spinner("📡 Загрузка новостей..."):
    try:
        news = fetch_news(rss_feeds[source])
        
        for entry in news:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### [{entry.title}]({entry.link})")
                    
                    # Описание
                    if hasattr(entry, 'summary'):
                        summary = entry.summary[:300] + "..." if len(entry.summary) > 300 else entry.summary
                        st.markdown(f"{summary}")
                    
                    # Дата
                    if hasattr(entry, 'published'):
                        st.caption(f"📅 {entry.published}")
                
                with col2:
                    # Теги (если есть)
                    if hasattr(entry, 'tags'):
                        for tag in entry.tags[:3]:
                            st.caption(f"🏷️ {tag.term}")
                
                st.markdown("---")
    except Exception as e:
        st.error(f"❌ Ошибка загрузки новостей: {e}")

# Кнопка возврата
if st.button("🏠 На главную", use_container_width=True):
    st.switch_page("main.py")