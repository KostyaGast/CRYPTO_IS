"""
Страница новостей криптовалют с картинками.
"""
import streamlit as st
import feedparser
from datetime import datetime
import re

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

# ============================================
# ЗАГОЛОВОК
# ============================================
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="font-size: 42px; font-weight: bold; background: linear-gradient(135deg, #F7931A, #627EEA, #00ff88); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        📰 Новости криптовалют
    </h1>
    <p style="color: #888; font-size: 16px;">Актуальные новости из мира криптовалют и финансов</p>
</div>
""", unsafe_allow_html=True)

# Словарь с источниками
rss_feeds = {
    "CoinTelegraph (EN)": "https://cointelegraph.com/rss",
    "CoinDesk (EN)": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Decrypt (EN)": "https://decrypt.co/feed",
    "🇷🇺 ForkLog": "https://forklog.com/feed",
    "🇷🇺 Tproger": "https://tproger.ru/feed/",
    "🇷🇺 3DNews": "https://3dnews.ru/news/rss",
    "🇷🇺 Хабр": "https://habr.com/ru/rss/news/?fl=ru",
}

# ============================================
# CSS СТИЛИ
# ============================================
st.markdown("""
<style>
    .news-card {
        background: linear-gradient(135deg, #1a1c23, #1e2130);
        border: 1px solid #2a2d3a;
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        border-color: #F7931A;
    }
    .news-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #F7931A, #627EEA);
        border-radius: 4px 0 0 4px;
    }
    .news-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 12px;
        line-height: 1.4;
    }
    .news-title a {
        color: #ffffff;
        text-decoration: none;
    }
    .news-title a:hover {
        color: #F7931A;
    }
    .news-meta {
        color: #888;
        font-size: 13px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 15px;
        flex-wrap: wrap;
    }
    .news-meta span {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .news-tag {
        display: inline-block;
        background: rgba(247, 147, 26, 0.15);
        color: #F7931A;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 6px;
        border: 1px solid rgba(247, 147, 26, 0.3);
    }
    .news-description {
        color: #aaa;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 15px;
    }
    .news-description img {
        max-width: 100%;
        border-radius: 10px;
        margin: 12px 0;
    }
    .read-more {
        display: inline-block;
        background: linear-gradient(135deg, #F7931A, #e67e22);
        color: white;
        padding: 8px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 14px;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    .read-more:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(247, 147, 26, 0.4);
    }
    .loading-spinner {
        text-align: center;
        padding: 50px;
    }
    .error-message {
        background: rgba(255, 68, 68, 0.1);
        border: 1px solid #ff4444;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)

# Выбор источника
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    source = st.selectbox(
        "📡 Источник",
        list(rss_feeds.keys()),
        label_visibility="collapsed"
    )

# ============================================
# ЗАГРУЗКА НОВОСТЕЙ
# ============================================
@st.cache_data(ttl=600)
def fetch_news(feed_url):
    """Загружает новости из RSS."""
    try:
        feed = feedparser.parse(feed_url)
        return feed.entries[:15]
    except:
        return None

with st.spinner("📡 Загрузка новостей..."):
    news = fetch_news(rss_feeds[source])

# ============================================
# ОТОБРАЖЕНИЕ НОВОСТЕЙ
# ============================================
if news is None:
    st.markdown("""
    <div class="error-message">
        <h2>❌ Ошибка загрузки</h2>
        <p>Не удалось загрузить новости. Попробуйте позже или выберите другой источник.</p>
    </div>
    """, unsafe_allow_html=True)
elif len(news) == 0:
    st.markdown("""
    <div class="error-message">
        <h2>📭 Нет новостей</h2>
        <p>По выбранному источнику нет новостей. Попробуйте другой.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"### 🔥 Найдено {len(news)} новостей")
    
    for entry in news:
        # Заголовок
        title = entry.title if hasattr(entry, 'title') else "Без названия"
        
        # Ссылка
        link = entry.link if hasattr(entry, 'link') else "#"
        
        # Дата
        if hasattr(entry, 'published'):
            try:
                date_obj = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                date_str = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = entry.published[:25]
        else:
            date_str = "—"
        
        # Автор
        author = entry.author if hasattr(entry, 'author') else "Неизвестен"
        
        # Описание
        summary = ""
        if hasattr(entry, 'summary'):
            # Убираем HTML-теги для превью
            summary = re.sub(r'<[^>]+>', '', entry.summary)
            summary = summary[:300] + "..." if len(summary) > 300 else summary
        
        # Теги
        tags = []
        if hasattr(entry, 'tags'):
            for tag in entry.tags[:4]:
                tag_name = tag.term if hasattr(tag, 'term') else str(tag)
                tags.append(tag_name)
        
        # Изображение
        image_url = None
        if hasattr(entry, 'media_content') and entry.media_content:
            image_url = entry.media_content[0].get('url')
        elif hasattr(entry, 'links'):
            for link_item in entry.links:
                if 'image' in link_item.get('type', ''):
                    image_url = link_item.get('href')
                    break
        
        if not image_url and hasattr(entry, 'summary'):
            img_match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
            if img_match:
                image_url = img_match.group(1)
        
        # Формируем HTML карточки (БЕЗ f-строки с обратными слешами)
        st.markdown('<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="news-title"><a href="{link}" target="_blank">{title}</a></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="news-meta"><span>📅 {date_str}</span><span>✍️ {author}</span><span>📡 {source}</span></div>', unsafe_allow_html=True)
        
        if tags:
            tags_html = '<div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px;">'
            for tag in tags:
                tags_html += f'<span class="news-tag">{tag}</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)
        
        if image_url:
            st.markdown(f'<img src="{image_url}" style="max-width:100%; border-radius:12px; margin-bottom:12px; max-height:300px; object-fit:cover;" />', unsafe_allow_html=True)
        
        st.markdown(f'<div class="news-description">{summary}</div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{link}" target="_blank" class="read-more">📖 Читать полностью</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# ПОДВАЛ
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    if st.button("🏠 На главную", use_container_width=True):
        st.switch_page("main.py")

st.markdown(f"""
<div style="text-align: center; color: #666; padding: 15px; font-size: 13px;">
    <p>Новости предоставлены {source} | Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
</div>
""", unsafe_allow_html=True)