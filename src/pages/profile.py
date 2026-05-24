"""
Личный кабинет пользователя с полным набором настроек.
"""
import streamlit as st
import json
import hashlib
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from database import (
    get_user_by_id, update_user_password, link_yandex_to_user,
    get_connection, delete_user as db_delete_user
)
#from yandex_auth import get_yandex_auth_url

st.set_page_config(
    page_title="Личный кабинет | Crypto IS",
    page_icon="👤",
    layout="wide"
)

# ============================================
# ПРОВЕРКА АВТОРИЗАЦИИ
# ============================================
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Доступ только для авторизованных пользователей.")
    st.stop()

user = st.session_state["user"]

# ============================================
# ЗАГРУЗКА НАСТРОЕК ПОЛЬЗОВАТЕЛЯ
# ============================================
SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / f"settings_{user.get('id')}.json"
LOGINS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / f"logins_{user.get('id')}.json"
ALERTS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / f"alerts_{user.get('id')}.json"

def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "language": "ru",
        "theme": "dark",
        "currency": "USD",
        "avatar": user.get("picture", ""),
        "display_name": user.get("username", ""),
        "favorites": ["BTC", "ETH"],
        "notifications": True,
        "newsletter": False,
        "chart_type": "candlestick",
        "indicators": []
    }

def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def load_logins():
    if LOGINS_FILE.exists():
        with open(LOGINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_login(ip, device):
    logins = load_logins()
    logins.append({
        "timestamp": datetime.now().isoformat(),
        "ip": ip,
        "device": device
    })
    LOGINS_FILE.parent.mkdir(exist_ok=True)
    with open(LOGINS_FILE, "w", encoding="utf-8") as f:
        json.dump(logins[-50:], f, indent=2)

def load_alerts():
    if ALERTS_FILE.exists():
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_alerts(alerts):
    ALERTS_FILE.parent.mkdir(exist_ok=True)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

settings = load_settings()
alerts = load_alerts()

# ============================================
# ПЕРЕВОДЫ
# ============================================
translations = {
    "ru": {
        "title": "👤 Личный кабинет",
        "profile": "📋 Профиль",
        "security": "🔐 Безопасность",
        "appearance": "🎨 Оформление",
        "yandex": "🟣 Яндекс ID",
        "favorites": "⭐ Избранное",
        "alerts": "🔔 Уведомления",
        "sessions": "📱 Сессии",
        "export": "📤 Экспорт",
        "danger": "⚠️ Опасная зона",
        "main_info": "Основная информация",
        "username": "Имя пользователя",
        "email": "Email",
        "current_password": "Текущий пароль",
        "new_password": "Новый пароль",
        "confirm_password": "Подтвердите пароль",
        "change_password": "💾 Сменить пароль",
        "change_email": "📧 Сменить email",
        "new_email": "Новый email",
        "language": "Язык интерфейса",
        "theme": "Тема",
        "currency": "Валюта отображения",
        "chart_type": "Тип графика",
        "indicators": "Индикаторы",
        "light": "☀️ Светлая",
        "dark": "🌙 Тёмная",
        "save_settings": "💾 Сохранить настройки",
        "yandex_linked": "✅ Яндекс ID привязан",
        "link_yandex": "🔗 Привязать Яндекс ID",
        "unlink_yandex": "🔓 Отвязать Яндекс ID",
        "avatar": "Аватар",
        "avatar_url": "URL аватара",
        "display_name": "Отображаемое имя",
        "back": "🏠 На главную",
        "logout": "🚪 Выйти",
        "save_success": "✅ Настройки сохранены",
        "password_changed": "✅ Пароль успешно изменён",
        "email_changed": "✅ Email успешно изменён",
        "error": "❌ Ошибка",
        "fill_fields": "Заполните все поля",
        "password_min": "Пароль должен быть не менее 6 символов",
        "passwords_match": "Пароли не совпадают",
        "wrong_password": "Неверный текущий пароль",
        "delete_account": "🗑️ Удалить аккаунт",
        "delete_warning": "Это действие нельзя отменить! Все ваши данные будут удалены.",
        "confirm_delete": "✅ Да, удалить",
        "cancel": "❌ Отмена",
        "export_data": "📥 Скачать мои данные",
        "favorites_desc": "Выберите избранные криптовалюты для быстрого доступа",
        "notifications": "🔔 Email-уведомления",
        "notifications_desc": "Получать уведомления о входе с новых устройств",
        "newsletter": "📧 Рассылка",
        "newsletter_desc": "Получать новости и обновления",
        "price_alert": "💰 Ценовые алерты",
        "add_alert": "➕ Добавить алерт",
        "alert_asset": "Актив",
        "alert_condition": "Условие",
        "alert_price": "Цена (USD)",
        "active_alerts": "Активные алерты",
        "no_alerts": "Нет активных алертов",
        "delete": "Удалить",
        "session_history": "История входов",
        "date": "Дата",
        "ip_address": "IP адрес",
        "device": "Устройство",
        "no_sessions": "Нет данных о входах",
        "2fa": "🔐 Двухфакторная аутентификация",
        "2fa_desc": "В разработке...",
        "total_logins": "Всего входов",
        "member_since": "Пользователь с",
        "telegram": "📱 Telegram",
        "telegram_linked": "✅ Telegram привязан",
        "telegram_not_linked": "🔗 Привяжите Telegram для получения уведомлений",
        "telegram_code": "Код привязки",
        "telegram_instruction": "Отправьте этот код боту @crypto_is_notify_bot",
        "telegram_unlink": "🔓 Отвязать Telegram",
        "telegram_generate": "🔄 Сгенерировать новый код",
    },
    "en": {
        "title": "👤 Profile",
        "profile": "📋 Profile",
        "security": "🔐 Security",
        "appearance": "🎨 Appearance",
        "yandex": "🟣 Yandex ID",
        "favorites": "⭐ Favorites",
        "alerts": "🔔 Alerts",
        "sessions": "📱 Sessions",
        "export": "📤 Export",
        "danger": "⚠️ Danger Zone",
        "main_info": "Main Information",
        "username": "Username",
        "email": "Email",
        "current_password": "Current password",
        "new_password": "New password",
        "confirm_password": "Confirm password",
        "change_password": "💾 Change password",
        "change_email": "📧 Change email",
        "new_email": "New email",
        "language": "Interface language",
        "theme": "Theme",
        "currency": "Display currency",
        "chart_type": "Chart type",
        "indicators": "Indicators",
        "light": "☀️ Light",
        "dark": "🌙 Dark",
        "save_settings": "💾 Save settings",
        "yandex_linked": "✅ Yandex ID linked",
        "link_yandex": "🔗 Link Yandex ID",
        "unlink_yandex": "🔓 Unlink Yandex ID",
        "avatar": "Avatar",
        "avatar_url": "Avatar URL",
        "display_name": "Display name",
        "back": "🏠 Back to main",
        "logout": "🚪 Log out",
        "save_success": "✅ Settings saved",
        "password_changed": "✅ Password changed",
        "email_changed": "✅ Email changed",
        "error": "❌ Error",
        "fill_fields": "Fill all fields",
        "password_min": "Password must be at least 6 characters",
        "passwords_match": "Passwords do not match",
        "wrong_password": "Wrong current password",
        "delete_account": "🗑️ Delete account",
        "delete_warning": "This action cannot be undone! All your data will be deleted.",
        "confirm_delete": "✅ Yes, delete",
        "cancel": "❌ Cancel",
        "export_data": "📥 Download my data",
        "favorites_desc": "Select favorite cryptocurrencies for quick access",
        "notifications": "🔔 Email notifications",
        "notifications_desc": "Get notified about logins from new devices",
        "newsletter": "📧 Newsletter",
        "newsletter_desc": "Receive news and updates",
        "price_alert": "💰 Price alerts",
        "add_alert": "➕ Add alert",
        "alert_asset": "Asset",
        "alert_condition": "Condition",
        "alert_price": "Price (USD)",
        "active_alerts": "Active alerts",
        "no_alerts": "No active alerts",
        "delete": "Delete",
        "session_history": "Login history",
        "date": "Date",
        "ip_address": "IP address",
        "device": "Device",
        "no_sessions": "No login data",
        "2fa": "🔐 Two-factor authentication",
        "2fa_desc": "Coming soon...",
        "total_logins": "Total logins",
        "member_since": "Member since",
        "telegram": "📱 Telegram",
        "telegram_linked": "✅ Telegram linked",
        "telegram_not_linked": "🔗 Link Telegram to receive notifications",
        "telegram_code": "Link code",
        "telegram_instruction": "Send this code to @crypto_is_notify_bot",
        "telegram_unlink": "🔓 Unlink Telegram",
        "telegram_generate": "🔄 Generate new code",
    }
}

lang = settings.get("language", "ru")
t = translations[lang]

# ============================================
# ЗАГОЛОВОК И СТАТИСТИКА
# ============================================
st.title(t["title"])

logins = load_logins()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(t["total_logins"], len(logins))
with col2:
    st.metric(t["member_since"], user.get("created_at", datetime.now().strftime("%Y-%m-%d"))[:10])
with col3:
    st.metric("🆔 ID", user.get("id"))

st.markdown("---")

# ============================================
# ВКЛАДКИ
# ============================================
tabs = st.tabs([
    t["profile"], t["security"], t["appearance"], 
    t["sessions"], t["telegram"], t["export"], t["danger"], "📊 Отчёты"
])

# ============================================
# ВКЛАДКА 0: ПРОФИЛЬ
# ============================================
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(t["avatar"])
        current_avatar = settings.get("avatar") or user.get("picture") or "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp"
        st.image(current_avatar, width=200)
        new_avatar = st.text_input(t["avatar_url"], value=current_avatar, placeholder="https://...")
    
    with col2:
        st.subheader(t["main_info"])
        display_name = st.text_input(t["display_name"], value=settings.get("display_name", user.get("username", "")))
        st.text_input(t["email"], value=user.get("email", ""), disabled=True)
        st.caption(f"🆔 User ID: {user.get('id')}")
        st.caption(f"📅 {t['member_since']}: {user.get('created_at', '—')}")
    
    if st.button(t["save_settings"], use_container_width=True, key="save_profile"):
        settings["avatar"] = new_avatar
        settings["display_name"] = display_name
        save_settings(settings)
        st.session_state["user"]["picture"] = new_avatar
        st.session_state["user"]["username"] = display_name
        st.success(t["save_success"])
        st.rerun()

# ============================================
# ВКЛАДКА 1: БЕЗОПАСНОСТЬ
# ============================================
with tabs[1]:
    col1, col2 = st.columns(2)
    
with col1:
    st.subheader(t["change_password"])
    
    if st.session_state.get("auth_method") == "sqlite":
        with st.form("change_password_form"):
            current_password = st.text_input(t["current_password"], type="password")
            new_password = st.text_input(t["new_password"], type="password")
            confirm_password = st.text_input(t["confirm_password"], type="password")
            
            if st.form_submit_button(t["change_password"], use_container_width=True):
                if not current_password or not new_password or not confirm_password:
                    st.error(t["fill_fields"])
                elif len(new_password) < 6:
                    st.error(t["password_min"])
                elif new_password != confirm_password:
                    st.error(t["passwords_match"])
                else:
                    from database import login_user
                    success, msg, _ = login_user(user["username"], current_password)
                    if not success:
                        st.error(t["wrong_password"])
                    else:
                        success, msg = update_user_password(user["id"], new_password)
                        if success:
                            st.success(t["password_changed"])
                        else:
                            st.error(f"{t['error']}: {msg}")
    else:
        st.info("🔑 Вы вошли через OAuth. Смена пароля недоступна.")
    with col2:
        st.subheader(t["change_email"])
        
        if st.session_state.get("auth_method") == "sqlite":
            with st.form("change_email_form"):
                new_email = st.text_input(t["new_email"], placeholder="new@email.com")
                password_confirm = st.text_input(t["current_password"], type="password")
                
                if st.form_submit_button(t["change_email"], use_container_width=True):
                    if not new_email or not password_confirm:
                        st.error(t["fill_fields"])
                    else:
                        from database import login_user, update_user_email
                        success, msg, _ = login_user(user["username"], password_confirm)
                        if not success:
                            st.error(t["wrong_password"])
                        else:
                            success, msg = update_user_email(user["id"], new_email)
                            if success:
                                st.session_state["user"]["email"] = new_email
                                st.success(t["email_changed"])
                            else:
                                st.error(msg)
        else:
            st.info("Смена email через OAuth недоступна.")
    
    st.markdown("---")
    st.subheader(t["2fa"])
    st.info(t["2fa_desc"])

# ============================================
# ВКЛАДКА 2: ОФОРМЛЕНИЕ
# ============================================
with tabs[2]:
    col1, col2 = st.columns(2)
    
    with col1:
        new_language = st.selectbox(
            t["language"],
            options=["ru", "en"],
            format_func=lambda x: "🇷🇺 Русский" if x == "ru" else "🇬🇧 English",
            index=0 if lang == "ru" else 1
        )
        
        new_currency = st.selectbox(
            t["currency"],
            options=["USD", "EUR", "RUB", "GBP", "JPY", "CNY"],
            index=["USD", "EUR", "RUB", "GBP", "JPY", "CNY"].index(settings.get("currency", "USD"))
        )
    
    with col2:  
        notifications = st.checkbox(t["notifications"], value=settings.get("notifications", True))
        st.caption(t["notifications_desc"])
        
        newsletter = st.checkbox(t["newsletter"], value=settings.get("newsletter", False))
        st.caption(t["newsletter_desc"])
    
    if st.button(t["save_settings"], use_container_width=True, key="save_appearance"):
        settings["language"] = new_language
        settings["currency"] = new_currency
        settings["notifications"] = notifications
        settings["newsletter"] = newsletter
        save_settings(settings)
        st.success(t["save_success"])
        st.rerun()
# ============================================
# ВКЛАДКА 3: СЕССИИ (ИСТОРИЯ ВХОДОВ)
# ============================================
with tabs[3]:
    st.subheader(t["session_history"])
    
    if logins:
        data = []
        for login in reversed(logins[-20:]):
            data.append({
                t["date"]: login["timestamp"][:19].replace("T", " "),
                t["ip_address"]: login["ip"],
                t["device"]: login["device"]
            })
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info(t["no_sessions"])

# ============================================
# ВКЛАДКА 4: TELEGRAM
# ============================================
with tabs[4]:
    st.subheader("📱 Telegram")
    
    from database import get_connection, generate_telegram_code, unlink_telegram
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_chat_id, telegram_verified, telegram_code FROM users WHERE id = ?", (user["id"],))
    tg_data = cursor.fetchone()
    conn.close()
    
    if tg_data and tg_data["telegram_verified"]:
        st.success(f"✅ Telegram привязан!")
        st.markdown(f"Chat ID: `{tg_data['telegram_chat_id']}`")
        
        if st.button("🔓 Отвязать Telegram", use_container_width=False):
            unlink_telegram(user["id"])
            st.rerun()
    else:
        st.info("🔗 Привяжите Telegram для получения уведомлений о входах и алертах.")
        
        # Генерируем или показываем существующий код
        if not tg_data or not tg_data["telegram_code"]:
            code = generate_telegram_code(user["id"])
        else:
            code = tg_data["telegram_code"]
        
        st.markdown(f"""
        ### Ваш код привязки:
        # <h1 style="font-family: monospace; background: #1a1c23; padding: 15px; border-radius: 10px; text-align: center;">{code}</h1>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        📱 <b>Как привязать:</b>
        1. Откройте Telegram и найдите бота <a href="https://t.me/crypto_is_notify_bot" target="_blank">@crypto_is_notify_bot</a>
        2. Отправьте боту команду <code>/start</code>
        3. Отправьте боту этот код: <code>{code}</code>
        4. Готово! Вы будете получать уведомления.
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Сгенерировать новый код"):
            code = generate_telegram_code(user["id"])
            st.rerun()
        
        # Кнопка открытия бота
        st.link_button("🚀 Открыть бота в Telegram", "https://t.me/crypto_is_notify_bot", use_container_width=True)


# ============================================
# ВКЛАДКА 5: ЭКСПОРТ ДАННЫХ
# ============================================
with tabs[5]:
    st.subheader(t["export_data"])
    
    if st.button(t["export_data"], use_container_width=True):
        export_data = {
            "user": {
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "created_at": user.get("created_at")
            },
            "settings": settings,
            "logins": logins,
            "alerts": alerts,
            "exported_at": datetime.now().isoformat()
        }
        
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Скачать JSON",
            data=json_data,
            file_name=f"crypto_is_export_{user.get('id')}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
# ============================================
# ВКЛАДКА 6: ОПАСНАЯ ЗОНА (УДАЛЕНИЕ АККАУНТА)
# ============================================
with tabs[6]:
    st.subheader(t["delete_account"])
    st.error(t["delete_warning"])
    
    if "confirm_delete" not in st.session_state:
        st.session_state["confirm_delete"] = False
    
    if not st.session_state["confirm_delete"]:
        if st.button(t["delete_account"], type="secondary", use_container_width=True):
            st.session_state["confirm_delete"] = True
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t["confirm_delete"], type="primary", use_container_width=True):
                db_delete_user(user["id"])
                if SETTINGS_FILE.exists():
                    SETTINGS_FILE.unlink()
                if LOGINS_FILE.exists():
                    LOGINS_FILE.unlink()
                if ALERTS_FILE.exists():
                    ALERTS_FILE.unlink()
                st.session_state.clear()
                st.switch_page("main.py")
        with col2:
            if st.button(t["cancel"], use_container_width=True):
                st.session_state["confirm_delete"] = False
                st.rerun()
# ============================================
# ВКЛАДКА 7: ОТЧЁТЫ
# ============================================
with tabs[7]:
    st.subheader("📊 Отчёты по историческим данным")
    
    from database import get_crypto_history, get_stock_history, get_available_crypto_symbols, get_available_stock_symbols, get_crypto_date_range, get_stock_date_range
    
    report_type = st.selectbox("Тип актива", ["Криптовалюта", "Акции"])
    
    if report_type == "Криптовалюта":
        available = get_available_crypto_symbols()
        if available:
            # Показываем красивые названия
            from config import config
            display_names = {v: k for k, v in config.SUPPORTED_COINS.items()}
            options = [display_names.get(s, s) for s in available]
            selected_display = st.selectbox("Выберите криптовалюту", options)
            coin_id = config.SUPPORTED_COINS.get(selected_display, available[options.index(selected_display)])
            
            min_date, max_date, count = get_crypto_date_range(coin_id)
            if count > 0:
                st.caption(f"📅 Доступно: {min_date} — {max_date} ({count} записей)")
        else:
            st.warning("Нет данных. Загрузите историю через data_loader.py")
            coin_id = None
    else:
        available = get_available_stock_symbols()
        if available:
            from stock_fetcher import WORLD_STOCKS
            display_names = {v: k for k, v in WORLD_STOCKS.items()}
            options = [display_names.get(s, s) for s in available]
            selected_display = st.selectbox("Выберите акцию", options)
            # Извлекаем чистый тикер из строки вида "🌍 Apple (AAPL)"
            if '(' in selected_display and ')' in selected_display:
                ticker = selected_display.split('(')[1].split(')')[0]
            else:
                ticker = selected_display            
            min_date, max_date, count = get_stock_date_range(ticker)
            if count > 0:
                st.caption(f"📅 Доступно: {min_date} — {max_date} ({count} записей)")
        else:
            st.warning("Нет данных. Загрузите историю через data_loader.py")
            ticker = None
    
    months = st.selectbox("Период", [1, 3, 6, 12], format_func=lambda x: f"{x} мес.")
    
    if st.button("📊 Сформировать отчёт", use_container_width=True, type="primary"):
        if report_type == "Криптовалюта" and coin_id:
            df = get_crypto_history(coin_id, months)
        elif report_type == "Акции" and ticker:
            df = get_stock_history(ticker, months)
        else:
            df = pd.DataFrame()
        
        if not df.empty:
            st.success(f"✅ Найдено {len(df)} записей")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close']))
            fig.update_layout(template="plotly_dark", height=400, title=f"График за {months} мес.")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="📥 Скачать CSV", data=csv, file_name=f"report_{months}months.csv", mime="text/csv")
        else:
            st.warning("Нет данных. Загрузите историю через data_loader.py")
# ============================================
# НАВИГАЦИЯ
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(t["back"], use_container_width=True):
        st.switch_page("main.py")

with col3:
    if st.button(t["logout"], use_container_width=True):
        import extra_streamlit_components as stx
        cookie_manager = stx.CookieManager()
        
        st.session_state["logout_triggered"] = True
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.session_state["auth_method"] = None
        
        try:
            cookie_manager.delete("crypto_is_user")
            cookie_manager.delete("crypto_is_auth_method")
        except:
            pass
        
        st.switch_page("main.py")