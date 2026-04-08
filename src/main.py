"""
Crypto IS - Главный GUI на Streamlit.
Аутентификация: Email/Password (SQLite) + Google OAuth.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os

from config import config
from fetcher import CryptoFetcher
from plotter import (
    create_candlestick_chart,
    create_performance_chart,
    create_volume_profile
)
from database import register_user, login_user

# Импорт для Google OAuth
from streamlit_google_auth import Authenticate

# ============================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================
st.set_page_config(
    page_title="Crypto IS - BTC/ETH Мониторинг",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# КОНФИГУРАЦИЯ GOOGLE AUTH
# ============================================
COOKIE_KEY = "2c48746ec28078ce015c1a82b9f5cdf1ba8af88efdaceef4c180866840723ca2"  # Замените на свой

authenticator = Authenticate(
    secret_credentials_path='google_credentials.json',
    cookie_name='crypto_is_session',
    cookie_key=COOKIE_KEY,
    redirect_uri='http://localhost:8501/oauth2callback',
)

# ВАЖНО: сначала проверяем авторизацию
if not st.session_state.get('connected', False):
    authenticator.check_authentification()

# ============================================
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "auth_method" not in st.session_state:
    st.session_state["auth_method"] = None

# Если вошли через Google
if st.session_state.get('connected', False):
    user_info = st.session_state.get('user_info', {})
    st.session_state["authenticated"] = True
    st.session_state["auth_method"] = "google"
    st.session_state["user"] = {
        "username": user_info.get('name') or user_info.get('email', 'Google User'),
        "email": user_info.get('email', ''),
        "picture": user_info.get('picture', '')
    }

# ============================================
# ФУНКЦИЯ ВЫХОДА
# ============================================
def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["auth_method"] = None
    authenticator.logout()

# ============================================
# ЭКРАН АУТЕНТИФИКАЦИИ
# ============================================
def auth_screen():
    """Экран входа: SQLite + Google."""
    
    st.markdown("""
    <div style="text-align: center; padding: 30px 0 10px 0;">
        <h1 style="background: linear-gradient(135deg, #F7931A, #627EEA); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent;
                   font-size: 52px;">
            📊 Crypto IS
        </h1>
        <p style="color: #aaa; font-size: 18px; margin-bottom: 30px;">
            Информационная система мониторинга Bitcoin и Ethereum
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📧 Email / Пароль", "🚀 Google", "📝 Регистрация"])
    
    # ===== Вкладка 1: Вход SQLite =====
        # ===== Вкладка 1: Вход SQLite =====
    with tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Вход в систему")
            username = st.text_input("Логин", key="login_username", placeholder="Введите логин или email")
            password = st.text_input("Пароль", type="password", key="login_password", placeholder="Введите пароль")
            
            # ДВЕ КНОПКИ В ОДНОЙ СТРОКЕ
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Войти", use_container_width=True, type="primary", key="login_btn"):
                    if not username or not password:
                        st.error("Заполните все поля")
                    else:
                        success, message, user_data = login_user(username, password)
                        if success:
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user_data
                            st.session_state["auth_method"] = "sqlite"
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            with col_btn2:
                if st.button("🔑 Забыли пароль?", use_container_width=True, key="forgot_btn"):
                    st.session_state["show_reset"] = True
                    st.rerun()

    # ===== Вкладка 2: Google =====
    with tab2:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Вход через Google")
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <p>Используйте ваш Google аккаунт</p>
            </div>
            """, unsafe_allow_html=True)
            
            auth_url = authenticator.get_authorization_url()
            st.link_button("🚀 Войти через Google", auth_url, use_container_width=True)
    
    # ===== Вкладка 3: Регистрация =====
    with tab3:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Создание аккаунта")
            new_username = st.text_input("Логин", key="reg_username", placeholder="Придумайте логин")
            new_email = st.text_input("Email (опционально)", key="reg_email", placeholder="your@email.com")
            new_password = st.text_input("Пароль", type="password", key="reg_password", placeholder="Минимум 6 символов")
            new_password_confirm = st.text_input("Подтвердите пароль", type="password", key="reg_password_confirm")
            
            if st.button("Зарегистрироваться", use_container_width=True, type="primary", key="reg_btn"):
                if not new_username or not new_password:
                    st.error("Логин и пароль обязательны")
                elif len(new_password) < 6:
                    st.error("Пароль должен быть не менее 6 символов")
                elif new_password != new_password_confirm:
                    st.error("Пароли не совпадают")
                else:
                    success, message = register_user(new_username, new_password, new_email)
                    if success:
                        st.success(message + " Теперь войдите.")
                    else:
                        st.error(message)
    # ===== Вкладка 4: Сброс пароля (показывается только при необходимости) =====
    if st.session_state.get("show_reset", False):
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Восстановление пароля")
            
            # Шаг 1: Ввод email/логина
            if "reset_step" not in st.session_state:
                st.session_state["reset_step"] = 1
            
            if st.session_state["reset_step"] == 1:
                email_or_username = st.text_input("Email или логин", placeholder="Введите email или логин")
                
                if st.button("📧 Отправить код", use_container_width=True, type="primary"):
                    if not email_or_username:
                        st.error("Введите email или логин")
                    else:
                        from database import create_password_reset
                        from email_sender import send_reset_code
                        
                        success, message, email = create_password_reset(email_or_username)
                        if success:
                            # В реальном приложении здесь отправляется email
                            # Для демо покажем код на экране
                            st.session_state["reset_email"] = email
                            st.session_state["reset_step"] = 2
                            st.success(f"Код отправлен на {email}")
                            st.rerun()
                        else:
                            st.error(message)
            
            # Шаг 2: Ввод кода
            elif st.session_state["reset_step"] == 2:
                code = st.text_input("Код из письма", placeholder="Введите 6-значный код", max_chars=6)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Подтвердить", use_container_width=True, type="primary"):
                        from database import verify_reset_code
                        
                        success, message, user_id = verify_reset_code(
                            st.session_state["reset_email"], 
                            code
                        )
                        if success:
                            st.session_state["reset_user_id"] = user_id
                            st.session_state["reset_step"] = 3
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col2:
                    if st.button("🔄 Назад", use_container_width=True):
                        st.session_state["reset_step"] = 1
                        st.rerun()
            
            # Шаг 3: Новый пароль
            elif st.session_state["reset_step"] == 3:
                new_password = st.text_input("Новый пароль", type="password", placeholder="Минимум 6 символов")
                new_password_confirm = st.text_input("Подтвердите пароль", type="password")
                
                if st.button("💾 Сохранить пароль", use_container_width=True, type="primary"):
                    if not new_password or len(new_password) < 6:
                        st.error("Пароль должен быть не менее 6 символов")
                    elif new_password != new_password_confirm:
                        st.error("Пароли не совпадают")
                    else:
                        from database import reset_password
                        
                        success, message = reset_password(st.session_state["reset_user_id"], new_password)
                        if success:
                            st.success(message + " Теперь вы можете войти.")
                            st.session_state["show_reset"] = False
                            st.session_state["reset_step"] = 1
                            st.rerun()
                        else:
                            st.error(message)
            
            if st.button("❌ Отмена", use_container_width=True):
                st.session_state["show_reset"] = False
                st.session_state["reset_step"] = 1
                st.rerun()

# ============================================
# ГЛАВНАЯ ЛОГИКА
# ============================================
if not st.session_state["authenticated"]:
    auth_screen()
    st.stop()

# ============================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ (только для авторизованных)
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #F7931A, #627EEA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .info-box {
        background: rgba(0,255,136,0.1);
        border-left: 4px solid #00ff88;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# САЙДБАР
# ============================================
with st.sidebar:
    st.title("🎛️ Управление")
    
    user = st.session_state["user"]
    if st.session_state["auth_method"] == "google":
        if user.get("picture"):
            st.image(user["picture"], width=50)
        st.markdown(f"👤 **{user['username']}** (Google)")
    else:
        st.markdown(f"👤 **{user['username']}**")
    
    if user.get("email"):
        st.caption(f"📧 {user['email']}")
    
    st.markdown("---")
    
    coin_display = st.selectbox(
        "📌 Выберите криптовалюту",
        list(config.SUPPORTED_COINS.keys())
    )
    coin_id = config.SUPPORTED_COINS[coin_display]
    coin_symbol = "BTC" if "BTC" in coin_display else "ETH"
    coin_color = "#F7931A" if coin_symbol == "BTC" else "#627EEA"
    
    days_options = [1, 7, 14, 30, 90]
    days = st.selectbox("📅 Глубина истории", options=days_options, index=3)
    
    col1, col2 = st.columns(2)
    with col1:
        refresh = st.button("🔄 Обновить", use_container_width=True)
    with col2:
        force_refresh = st.button("⚠️ Принудительно", use_container_width=True)
    
    st.markdown("---")
    
    # Кнопка выхода
    if st.button("🚪 Выйти", use_container_width=True):
        logout()
        st.rerun()

# ============================================
# ОСНОВНАЯ ОБЛАСТЬ
# ============================================
st.markdown(f'<h1 class="main-header">📊 {coin_display} — Информационная система</h1>', 
            unsafe_allow_html=True)

fetcher = CryptoFetcher(coin_id=coin_id, days=days)

with st.spinner(f"Загрузка данных за {days} дней..."):
    if force_refresh:
        st.cache_data.clear()
    df = fetcher.get_data(force_refresh=refresh or force_refresh)

if df.empty:
    st.error("❌ Не удалось загрузить данные")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)
current = df["close"].iloc[-1]
prev = df["close"].iloc[-2] if len(df) > 1 else current
change = current - prev
change_pct = (change / prev) * 100 if prev > 0 else 0

col1.metric("💰 Текущая цена", f"${current:,.2f}", f"{change_pct:+.2f}%")
col2.metric("📊 Максимум", f"${df['high'].max():,.2f}")
col3.metric("📉 Минимум", f"${df['low'].min():,.2f}")
col4.metric("📊 Средняя", f"${df['close'].mean():,.2f}")
col5.metric("📅 Торговых дней", len(df))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📈 Свечной график", "📉 Доходность", "📋 Таблица"])

with tab1:
    st.plotly_chart(
        create_candlestick_chart(df, f"{coin_symbol} — Свечи (ПН-ПТ)", coin_color),
        use_container_width=True
    )

with tab2:
    st.plotly_chart(
        create_performance_chart(df, f"{coin_symbol} — Доходность"),
        use_container_width=True
    )

with tab3:
    display_df = df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values("date", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Скачать CSV",
        data=csv,
        file_name=f"{coin_symbol}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;padding:20px;'>© 2026 Crypto IS</div>", 
            unsafe_allow_html=True)