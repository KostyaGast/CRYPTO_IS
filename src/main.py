"""
Crypto IS - Главный GUI на Streamlit.
Аутентификация: Email/Пароль (SQLite).
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.io as pio
import json
from pathlib import Path
import extra_streamlit_components as stx

from config import config
from fetcher import CryptoFetcher
from stock_fetcher import StockFetcher
from plotter import (
    create_candlestick_chart,
    create_performance_chart,
)
from database import register_user, login_user

# ============================================
# GOOGLE OAUTH
# ============================================
import os

# Если есть secrets.toml — используем его, иначе локальный режим
if os.path.exists('.streamlit/secrets.toml'):
    # Серверный режим с Google OAuth
    USE_GOOGLE_AUTH = True
else:
    # Локальный режим без Google
    USE_GOOGLE_AUTH = False

# Менеджер для работы с cookies
cookie_manager = stx.CookieManager()

# ============================================
# КУРСЫ ВАЛЮТ И КОНВЕРТАЦИЯ
# ============================================
exchange_rates = {
    "USD": 1, 
    "EUR": 0.92, 
    "RUB": 92, 
    "GBP": 0.79, 
    "JPY": 150, 
    "CNY": 7.2
}

def convert_price(price_usd, currency="USD"):
    """Конвертирует цену из USD в выбранную валюту."""
    if price_usd is None:
        return 0
    return price_usd * exchange_rates.get(currency, 1)

def get_currency_symbol(currency):
    """Возвращает символ валюты."""
    symbols = {"USD": "$", "EUR": "€", "RUB": "₽", "GBP": "£", "JPY": "¥", "CNY": "¥"}
    return symbols.get(currency, "$")

# ============================================
# ПЕРЕВОДЫ
# ============================================
translations = {
    "ru": {
        "title": "📊 Crypto IS",
        "subtitle": "Информационная система мониторинга мировых финансов",
        "control": "🎛️ Управление",
        "asset_type": "📂 Тип актива",
        "crypto": "Криптовалюта",
        "stocks": "Акции",
        "futures": "Фьючерсы и фонды",
        "select_crypto": "📌 Выберите криптовалюту",
        "select_stock": "📌 Выберите акцию",
        "select_future": "📌 Выберите фьючерс/фонд",
        "depth": "📅 Глубина истории",
        "refresh": "🔄 Обновить",
        "logout": "🚪 Выйти",
        "profile": "👤 Личный кабинет",
        "current_price": "💰 Текущая цена",
        "max": "📊 Максимум",
        "min": "📉 Минимум",
        "avg": "📊 Средняя",
        "trading_days": "📅 Торговых дней",
        "candlestick": "📈 Свечной график",
        "performance": "📉 Доходность",
        "table": "📋 Таблица",
        "download": "📥 Скачать CSV",
        "loading": "🔄 Загрузка данных...",
        "error_load": "❌ Не удалось загрузить данные",
        "login_email": "📧 Email / Пароль",
        "register": "📝 Регистрация",
        "login_btn": "Войти",
        "forgot": "🔑 Забыли пароль?",
        "footer": "© 2026 Crypto IS — Информационная система мировых финансов",
        "info_box": "📋 Алгоритм работы",
        "info_text": "Данные с CoinGecko API • Только будние дни (ПН-ПТ) • Кэширование на 1 час"
    },
    "en": {
        "title": "📊 Crypto IS",
        "subtitle": "Global Financial Monitoring System",
        "control": "🎛️ Control",
        "asset_type": "📂 Asset type",
        "crypto": "Cryptocurrency",
        "stocks": "Stocks",
        "futures": "Futures & Funds",
        "select_crypto": "📌 Select cryptocurrency",
        "select_stock": "📌 Select stock",
        "select_future": "📌 Select future/fund",
        "depth": "📅 History depth",
        "refresh": "🔄 Refresh",
        "logout": "🚪 Log out",
        "profile": "👤 Profile",
        "current_price": "💰 Current price",
        "max": "📊 Maximum",
        "min": "📉 Minimum",
        "avg": "📊 Average",
        "trading_days": "📅 Trading days",
        "candlestick": "📈 Candlestick",
        "performance": "📉 Performance",
        "table": "📋 Table",
        "download": "📥 Download CSV",
        "loading": "🔄 Loading data...",
        "error_load": "❌ Failed to load data",
        "login_email": "📧 Email / Password",
        "register": "📝 Register",
        "login_btn": "Login",
        "forgot": "🔑 Forgot password?",
        "footer": "© 2026 Crypto IS — Global Financial Monitoring System",
        "info_box": "📋 Algorithm",
        "info_text": "CoinGecko API • Weekdays only (Mon-Fri) • 1 hour cache"
    },
    "zh": { 
        "title": "📊 Crypto IS",
        "subtitle": "全球金融监控系统",
        "control": "🎛️ 控制面板",
        "asset_type": "📂 资产类型",
        "crypto": "加密货币",
        "stocks": "股票",
        "futures": "期货与基金",
        "select_crypto": "📌 选择加密货币",
        "select_stock": "📌 选择股票",
        "select_future": "📌 选择期货/基金",
        "depth": "📅 历史深度",
        "refresh": "🔄 刷新",
        "logout": "🚪 退出",
        "profile": "👤 个人资料",
        "current_price": "💰 当前价格",
        "max": "📊 最高",
        "min": "📉 最低",
        "avg": "📊 平均",
        "trading_days": "📅 交易日",
        "candlestick": "📈 K线图",
        "performance": "📉 收益率",
        "table": "📋 数据表",
        "download": "📥 下载CSV",
        "loading": "🔄 加载数据中...",
        "error_load": "❌ 无法加载数据",
        "login_email": "📧 邮箱 / 密码",
        "register": "📝 注册",
        "login_btn": "登录",
        "forgot": "🔑 忘记密码？",
        "footer": "© 2026 Crypto IS — 全球金融监控系统",
        "info_box": "📋 算法说明",
        "info_text": "CoinGecko API • 仅工作日（周一至周五）• 1小时缓存"
    }
}

# ============================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================
st.set_page_config(
    page_title="Crypto IS - Мониторинг",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ПРОВЕРКА GOOGLE OAUTH (С ПРИНУДИТЕЛЬНЫМ РЕДИРЕКТОМ)
# ============================================
if USE_GOOGLE_AUTH and hasattr(st, 'experimental_user') and st.experimental_user.is_logged_in:
    user_info = st.experimental_user
    google_email = user_info.get("email", "")
    google_name = user_info.get("name", "Google User")
    google_picture = user_info.get("picture", "")

    from database import get_user_by_email, get_connection

    existing_user = get_user_by_email(google_email)

    if existing_user:
        st.session_state["authenticated"] = True
        st.session_state["auth_method"] = "google"
        st.session_state["user"] = existing_user
    else:
        base_username = google_email.split("@")[0].replace(".", "_")
        conn = get_connection()
        cursor = conn.cursor()

        final_username = base_username
        counter = 1
        while True:
            cursor.execute("SELECT id FROM users WHERE username = ?", (final_username,))
            if not cursor.fetchone():
                break
            final_username = f"{base_username}_{counter}"
            counter += 1

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, '')",
            (final_username, google_email)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        st.session_state["authenticated"] = True
        st.session_state["auth_method"] = "google"
        st.session_state["user"] = {
            "id": user_id,
            "username": final_username,
            "email": google_email,
            "picture": google_picture
        }

    # Принудительная перезагрузка страницы для применения сессии
    st.markdown("""
        <meta http-equiv="refresh" content="0; url=/">
    """, unsafe_allow_html=True)
    st.stop()
# Анимация загрузки страницы
st.markdown('<div class="fade-in">', unsafe_allow_html=True)

# ============================================
# ПРОВЕРКА СОХРАНЕННОЙ СЕССИИ (АВТОВХОД)
# ============================================
if "logout_triggered" not in st.session_state:
    st.session_state["logout_triggered"] = False

if not st.session_state.get("authenticated", False):
    if not st.session_state.get("logout_triggered", False):
        saved_user = cookie_manager.get("crypto_is_user")
        if saved_user:
            st.session_state["authenticated"] = True
            auth_method = cookie_manager.get("crypto_is_auth_method")
            st.session_state["auth_method"] = auth_method if auth_method else "sqlite"
            st.session_state["user"] = saved_user
            st.rerun()

# ============================================
# НАСТРОЙКА PLOTLY
# ============================================
pio.templates.default = "plotly_dark"

# ============================================
# ЗАГРУЗКА НАСТРОЕК ПОЛЬЗОВАТЕЛЯ
# ============================================
def load_user_settings(user_id):
    """Загружает настройки пользователя."""
    if user_id:
        settings_file = Path(__file__).resolve().parent.parent / "data" / f"settings_{user_id}.json"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
    return {
        "language": "ru",
        "theme": "dark",
        "currency": "USD",
        "favorites": ["BTC", "ETH"],
        "avatar": "",
        "display_name": ""
    }

# ============================================
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "auth_method" not in st.session_state:
    st.session_state["auth_method"] = None
if "show_reset" not in st.session_state:
    st.session_state["show_reset"] = False
if "alerts_monitoring_started" not in st.session_state:
    st.session_state["alerts_monitoring_started"] = False

# ============================================
# ЗАГРУЗКА НАСТРОЕК ПОСЛЕ АВТОРИЗАЦИИ
# ============================================
if st.session_state.get("authenticated"):
    user_id = st.session_state["user"].get("id")
    user_settings = load_user_settings(user_id)
else:
    user_settings = {"language": "ru", "currency": "USD", "theme": "dark", "favorites": ["BTC", "ETH"]}

lang = user_settings.get("language", "ru")
t = translations[lang]
currency = user_settings.get("currency", "USD")
currency_symbol = get_currency_symbol(currency)

# ============================================
# CSS СТИЛИ
# ============================================
st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #F7931A, #627EEA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }}
    .info-box {{
        background: rgba(0,255,136,0.1);
        border-left: 4px solid #00ff88;
        padding: 15px;
        border-radius: 5px;
    }}
    @media (max-width: 768px) {{
        .main-header {{
            font-size: 1.8rem !important;
        }}
        .stMetric {{
            font-size: 0.9rem !important;
        }}
    }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 14px !important;
        padding: 8px !important;
    }}
    .stPlotlyChart {{
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        padding: 10px;
        background: #1a1c23;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    button:hover {{
        transform: scale(1.02);
        transition: transform 0.2s ease;
    }}
    .stMetric:hover {{
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        transition: background 0.3s ease;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================
# ФУНКЦИЯ ВЫХОДА
# ============================================
def logout():
    st.session_state["logout_triggered"] = True
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["auth_method"] = None
    
    # Очистка Google OAuth сессии
    if hasattr(st, 'logout'):
        st.logout()
    
    try:
        cookie_manager.delete("crypto_is_user")
        cookie_manager.delete("crypto_is_auth_method")
    except:
        pass
    st.query_params.clear()
    st.rerun()

# ============================================
# ЭКРАН АУТЕНТИФИКАЦИИ
# ============================================
def auth_screen():
    # Если уже авторизован — не показываем форму
    if st.session_state.get("authenticated", False):
        return
    
    st.markdown(f"""
    <div style="text-align: center; padding: 30px 0 10px 0;">
        <h1 style="background: linear-gradient(135deg, #F7931A, #627EEA); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent;
                   font-size: 52px;">
            {t['title']}
        </h1>
        <p style="color: #aaa; font-size: 18px; margin-bottom: 30px;">
            {t['subtitle']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ОДНА КОЛОНКА ПО ЦЕНТРУ
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Вкладки для Email/Пароль и Регистрация
        tab1, tab2 = st.tabs([t["login_email"], t["register"]])
        
        # ===== ВКЛАДКА 1: Email/Пароль =====
        with tab1:
            username = st.text_input("Логин или Email", key="login_username")
            password = st.text_input("Пароль", type="password", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button(t["login_btn"], use_container_width=True, type="primary"):
                    if not username or not password:
                        st.error("Заполните все поля")
                    else:
                        success, message, user_data = login_user(username, password)
                        if success:
                            st.session_state["logout_triggered"] = False
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user_data
                            st.session_state["auth_method"] = "sqlite"
                            
                            try:
                                from telegram_bot import send_login_notification
                                send_login_notification(user_data["id"], user_data["username"], "***.***.***.***")
                            except:
                                pass

                            if not st.session_state.get("cookie_saved", False):
                                cookie_manager.set("crypto_is_user", {
                                    "id": user_data["id"],
                                    "username": user_data["username"],
                                    "email": user_data["email"]
                                }, expires_at=datetime.now() + timedelta(days=1), key="cookie_user")
                                cookie_manager.set("crypto_is_auth_method", "sqlite", expires_at=datetime.now() + timedelta(days=1), key="cookie_auth")
                                st.session_state["cookie_saved"] = True
                                                        
                            try:
                                from pages.profile import save_login
                                save_login("***.***.***.***", "Web Browser")
                            except:
                                pass
                            
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            with col_btn2:
                if st.button(t["forgot"], use_container_width=True):
                    st.session_state["show_reset"] = True
                    st.rerun()
        
        # ===== ВКЛАДКА 2: Регистрация =====
        with tab2:
            new_username = st.text_input("Логин", key="reg_username")
            new_email = st.text_input("Email (опционально)", key="reg_email")
            new_password = st.text_input("Пароль", type="password", key="reg_password")
            new_password_confirm = st.text_input("Подтвердите пароль", type="password", key="reg_password_confirm")
            
            if st.button(t["register"], use_container_width=True, type="primary"):
                if not new_username or not new_password:
                    st.error("Логин и пароль обязательны")
                elif len(new_password) < 6:
                    st.error("Пароль должен быть не менее 6 символов")
                elif new_password != new_password_confirm:
                    st.error("Пароли не совпадают")
                else:
                    success, message = register_user(new_username, new_password, new_email)
                    if success:
                        success_login, msg_login, user_data = login_user(new_username, new_password)
                        if success_login:
                            st.session_state["logout_triggered"] = False
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user_data
                            st.session_state["auth_method"] = "sqlite"
                            st.success("✅ Регистрация успешна!")
                            st.rerun()
                        else:
                            st.success(message + " Теперь войдите.")
                    else:
                        st.error(message)
    
    # Сброс пароля (остаётся без изменений)
    if st.session_state.get("show_reset", False):
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Восстановление пароля")
            if "reset_step" not in st.session_state:
                st.session_state["reset_step"] = 1
            
            if st.session_state["reset_step"] == 1:
                email_or_username = st.text_input("Email или логин")
                if st.button("📧 Отправить код", use_container_width=True):
                    from database import create_password_reset
                    success, message, email = create_password_reset(email_or_username)
                    if success:
                        st.session_state["reset_email"] = email
                        st.session_state["reset_step"] = 2
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            elif st.session_state["reset_step"] == 2:
                code = st.text_input("Код из письма", max_chars=6)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Подтвердить"):
                        from database import verify_reset_code
                        success, message, user_id = verify_reset_code(st.session_state["reset_email"], code)
                        if success:
                            st.session_state["reset_user_id"] = user_id
                            st.session_state["reset_step"] = 3
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.button("🔄 Назад"):
                        st.session_state["reset_step"] = 1
                        st.rerun()
            
            elif st.session_state["reset_step"] == 3:
                new_password = st.text_input("Новый пароль", type="password")
                new_password_confirm = st.text_input("Подтвердите пароль", type="password")
                if st.button("💾 Сохранить"):
                    from database import reset_password
                    success, message = reset_password(st.session_state["reset_user_id"], new_password)
                    if success:
                        st.success(message)
                        st.session_state["show_reset"] = False
                        st.rerun()
                    else:
                        st.error(message)
            
            if st.button("❌ Отмена"):
                st.session_state["show_reset"] = False
                st.rerun()

# ============================================
# ГЛАВНАЯ ЛОГИКА
# ============================================
if not st.session_state["authenticated"]:
    auth_screen()
    st.stop()

# ============================================
# САЙДБАР
# ============================================
with st.sidebar:
    st.title(t["control"])
    
    user = st.session_state["user"]
    display_name = user_settings.get("display_name") or user.get("username", "Пользователь")
    avatar = user_settings.get("avatar") or user.get("picture", "")
    col1, col2 = st.columns([1, 3])
    with col1:
        if avatar: st.image(avatar, width=50)
        else: st.markdown("👤")
    with col2:
        st.markdown(f"**{display_name}**")
        if user.get("email"): st.caption(f"📧 {user['email']}")
    st.markdown("---")
    
    if st.button("👤 Профиль", use_container_width=True): st.switch_page("pages/profile.py")
    if st.button("📰 Новости", use_container_width=True): st.switch_page("pages/news.py")
    if st.button("🔔 Алерты", use_container_width=True): st.switch_page("pages/alerts.py")
    if st.button("📈 Терминал", use_container_width=True):
        st.switch_page("pages/terminal.py")
    st.markdown("---")

    # ===== ВЫБОР ТИПА АКТИВА =====
    asset_type = st.selectbox(
        t["asset_type"],
        [t["crypto"], t["stocks"], t["futures"]]
    )

    if asset_type == t["crypto"]:
        coin_display = st.selectbox(t["select_crypto"], list(config.SUPPORTED_COINS.keys()))
        coin_id = config.SUPPORTED_COINS[coin_display]
        symbol = "BTC" if "BTC" in coin_display else "ETH"
        color = "#F7931A" if symbol == "BTC" else "#627EEA"
        title = f"{coin_display} — {t['crypto']}"

    elif asset_type == t["stocks"]:
        from stock_fetcher import WORLD_STOCKS
        stock_display = st.selectbox(t["select_stock"], list(WORLD_STOCKS.keys()))
        symbol = WORLD_STOCKS[stock_display]
        color = "#00ff88"
        title = f"{stock_display} — {t['stocks']}"
        coin_id = None

    else:  # Фьючерсы и фонды
        from stock_fetcher import FUTURES, ETFS
        all_futures = {**FUTURES, **ETFS}
        future_display = st.selectbox(t["select_future"], list(all_futures.keys()))
        symbol = all_futures[future_display]
        color = "#ffaa00"
        title = f"{future_display} — {t['futures']}"
        coin_id = None

    # ===== ВЫБОР ПЕРИОДА =====
    period_option = st.selectbox(
        "📅 Период",
        ["1 день", "7 дней", "14 дней", "30 дней", "Своя дата"]
    )

        # ===== БЫСТРЫЕ КНОПКИ =====
    st.markdown("**⚡ Быстрый выбор:**")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    if "custom_start" not in st.session_state:
        st.session_state.custom_start = datetime.now() - timedelta(days=30)
    if "custom_end" not in st.session_state:
        st.session_state.custom_end = datetime.now()
    
    today = datetime.now()
    
    with col_q1:
        if st.button("📆 Прошлая неделя"):
            # Последняя ПОЛНАЯ неделя (пн-вс или просто сдвиг)
            st.session_state.custom_end = today - timedelta(days=today.weekday() + 1)  # последнее воскресенье
            st.session_state.custom_start = st.session_state.custom_end - timedelta(days=7)
            st.session_state.period_override = "Своя дата"
    
    with col_q2:
        if st.button("📅 Прошлый месяц"):
            # Первый день предыдущего месяца по последний день предыдущего месяца
            first_of_this_month = today.replace(day=1)
            last_of_prev_month = first_of_this_month - timedelta(days=1)
            first_of_prev_month = last_of_prev_month.replace(day=1)
            st.session_state.custom_start = first_of_prev_month
            st.session_state.custom_end = last_of_prev_month
            st.session_state.period_override = "Своя дата"
    
    with col_q3:
        if st.button("🗓️ Этот год"):
            st.session_state.custom_start = datetime(today.year, 1, 1)
            st.session_state.custom_end = today
            st.session_state.period_override = "Своя дата"
    
    with col_q4:
        if st.button("📊 Максимум"):
            st.session_state.custom_start = datetime(2020, 1, 1)
            st.session_state.custom_end = today
            st.session_state.period_override = "Своя дата"

    # Определяем период
    use_custom = period_option == "Своя дата" or st.session_state.get("period_override") == "Своя дата"
    
    if use_custom:
        start_date = st.date_input("С", value=st.session_state.custom_start)
        end_date = st.date_input("По", value=st.session_state.custom_end)
        days = (end_date - start_date).days
        if days < 1:
            days = 1
        # Сохраняем для синхронизации
        st.session_state.custom_start = start_date
        st.session_state.custom_end = end_date
        st.session_state.period_override = None
    else:
        days = int(period_option.split()[0])
        st.session_state.custom_start = datetime.now() - timedelta(days=days)
        st.session_state.custom_end = datetime.now()

    refresh = st.button(t["refresh"], use_container_width=True)
    st.markdown("---")


    # ===== ВИДЖЕТЫ (теперь не зависят от show_widgets) =====
    from widgets import fear_greed_widget, top_crypto_widget
    st.subheader("📊 Виджеты")
    show_widgets = st.checkbox("Показывать виджеты", value=True)
    if show_widgets:
        if asset_type == t["crypto"]:
            if "(" in symbol and ")" in symbol:
                clean_symbol = symbol.split("(")[1].split(")")[0]
            else: clean_symbol = symbol
            fear_greed_widget(asset_type, clean_symbol)
        else:
            fear_greed_widget(asset_type, symbol)
        top_crypto_widget()
    if st.button("🔄 Обновить виджеты", use_container_width=True):
        from widgets import refresh_widgets
        refresh_widgets()
        st.rerun()
    st.markdown("---")

    # ===== TELEGRAM =====
    st.subheader("📱 Telegram")
    st.markdown("""<a href="https://t.me/crypto_is_notify_bot" target="_blank"><button style="background: linear-gradient(135deg, #229ED9, #1C93E3); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">🚀 Открыть бота в Telegram</button></a>""", unsafe_allow_html=True)
    st.caption("Получайте уведомления о входах и алерты")
    st.markdown("---")
    
    # ===== ИНФОРМАЦИОННЫЙ БЛОК =====
    st.markdown(f"""<div class="info-box"><h4>{t['info_box']}</h4><p>{t['info_text']}</p></div>""", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button(t["logout"], use_container_width=True): logout()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# ОСНОВНАЯ ОБЛАСТЬ
# ============================================
st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)

# Загрузка данных
if asset_type == t["crypto"]:
    # Округление days до поддерживаемых CoinGecko значений
    allowed = [1, 7, 14, 30, 90, 180, 365]
    closest = min(allowed, key=lambda x: abs(x - days))
    if days > closest and closest < 365:
        closest = next((v for v in allowed if v >= days), 365)
    fetcher = CryptoFetcher(coin_id=coin_id, days=closest)
else:
    # Для произвольных дат используем всегда 1 месяц, потом отфильтруем
    if period_option == "Своя дата":
        period = "3mo" if days > 60 else "1mo"
    else:
        period_map = {1: "1d", 7: "5d", 14: "1mo", 30: "1mo"}
        period = period_map.get(days, "1mo")
    fetcher = StockFetcher(symbol=symbol, period=period)

with st.spinner(t["loading"]):
    if asset_type == t["crypto"]:
        df = fetcher.get_data(force_refresh=refresh)
    else:
        df = fetcher.get_data()
# Фильтрация по выбранным датам
if period_option == "Своя дата" and not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) + pd.Timedelta(days=1)
    df = df[(df['date'] >= start) & (df['date'] < end)]

if df.empty:
    st.error(t["error_load"])
    st.stop()

# ============================================
# МЕТРИКИ
# ============================================
col1, col2, col3, col4, col5 = st.columns(5)

current = convert_price(df["close"].iloc[-1], currency)
prev = convert_price(df["close"].iloc[-2], currency) if len(df) > 1 else current
change = current - prev
change_pct = (change / prev) * 100 if prev > 0 else 0

col1.metric(
    f"{t['current_price']} ({currency})",
    f"{currency_symbol}{current:,.2f}",
    f"{change_pct:+.2f}%"
)
col2.metric(t["max"], f"{currency_symbol}{convert_price(df['high'].max(), currency):,.2f}")
col3.metric(t["min"], f"{currency_symbol}{convert_price(df['low'].min(), currency):,.2f}")
col4.metric(t["avg"], f"{currency_symbol}{convert_price(df['close'].mean(), currency):,.2f}")
col5.metric(t["trading_days"], len(df))

st.markdown("---")

# ============================================
# ЗАПУСК МОНИТОРИНГА АЛЕРТОВ (ОДИН РАЗ)
# ============================================
if not st.session_state.get("alerts_monitoring_started", False):
    try:
        from alerts.checker import start_alerts_monitoring
        start_alerts_monitoring()
        st.session_state.alerts_monitoring_started = True
        print("✅ Мониторинг алертов запущен")
    except Exception as e:
        print(f"⚠️ Мониторинг алертов не запущен: {e}")


# ============================================
# ГРАФИКИ (Pro)
# ============================================
from pro_charts import create_pro_chart, create_order_book

tab1, tab2, tab3 = st.tabs(["📈 Pro-график", "📉 Доходность", "📊 Стакан"])

with tab1:
    fig = create_pro_chart(df, f"{symbol} — Pro-график", color)
    st.plotly_chart(fig, use_container_width=True, key="pro_chart")

    # Пояснения к индикаторам
    with st.expander("ℹ️ Что означают индикаторы RSI и MACD?"):
        st.markdown("""
        **RSI (Relative Strength Index)** – индекс относительной силы.
        - Показывает, перекуплен ли актив (выше 70) или перепродан (ниже 30).
        - Значения выше 70 могут говорить о скорой коррекции вниз, ниже 30 – о возможном росте.
        
        **MACD (Moving Average Convergence Divergence)** – схождение/расхождение скользящих средних.
        - Гистограмма выше нуля (зелёная) – бычий тренд, ниже (красная) – медвежий.
        - Пересечение линии MACD и сигнальной линии даёт сигналы на покупку/продажу.
        """)

with tab2:
    fig = create_performance_chart(df, f"{symbol} — Доходность")
    st.plotly_chart(fig, use_container_width=True, key="tab2_chart")

with tab3:
    st.markdown("### 📊 Стакан (Order Book)")
    #st.caption("🟢 Слева — покупка (Bid) | 🔴 Справа — продажа (Ask)")
    fig = create_order_book(df, f"{symbol} — Стакан", color)
    st.plotly_chart(fig, use_container_width=True, key="order_book")
# ============================================
# ПОДВАЛ
# ============================================
st.markdown("---")
st.markdown(f"<div style='text-align:center;color:#666;padding:20px;'>{t['footer']}</div>", unsafe_allow_html=True)