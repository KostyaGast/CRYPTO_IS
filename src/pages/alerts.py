"""
Страница управления ценовыми алертами
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_user_alerts, delete_alert, deactivate_alert

st.set_page_config(page_title="Алерты | Crypto IS", page_icon="🔔", layout="wide")

# Проверка авторизации
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Доступ только для авторизованных пользователей.")
    st.stop()

user = st.session_state["user"]

st.title("🔔 Управление ценовыми алертами")

# ============================================
# ФОРМА СОЗДАНИЯ АЛЕРТА
# ============================================
with st.expander("➕ Создать новый алерт", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.text_input("Актив (например: BTC, AAPL)", placeholder="BTC")
    
    with col2:
        condition = st.selectbox("Условие", ["Выше", "Ниже"])
        condition_en = "above" if condition == "Выше" else "below"
    
    with col3:
        target_price = st.number_input("Цена (USD)", min_value=0.01, step=10.0, value=50000.0)
    
    if st.button("🔔 Установить алерт", type="primary"):
        if symbol.strip():
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO price_alerts (user_id, symbol, condition, price)
                VALUES (?, ?, ?, ?)
            """, (user["id"], symbol.upper(), condition_en, target_price))
            conn.commit()
            conn.close()
            st.success(f"✅ Алерт для {symbol.upper()} установлен!")
            st.rerun()
        else:
            st.error("❌ Укажите актив")

# ============================================
# СПИСОК АКТИВНЫХ АЛЕРТОВ
# ============================================
st.subheader("📋 Мои алерты")

alerts = get_user_alerts(user["id"], active_only=True)

if alerts:
    for alert in alerts:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{alert['symbol']}**")
        with col2:
            condition_text = "🟢 Выше" if alert["condition"] == "above" else "🔴 Ниже"
            st.markdown(condition_text)
        with col3:
            st.markdown(f"${alert['price']:,.2f}")
        with col4:
            st.caption(alert["created_at"][:16])
        with col5:
            if st.button("❌", key=f"del_{alert['id']}"):
                delete_alert(alert["id"], user["id"])
                st.rerun()
        
        st.divider()
else:
    st.info("📭 У вас нет активных алертов. Создайте первый!")

# ============================================
# ИСТОРИЯ СРАБОТАВШИХ АЛЕРТОВ
# ============================================
st.subheader("📜 История сработавших алертов")

from database import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT * FROM price_alerts 
    WHERE user_id = ? AND active = 0
    ORDER BY created_at DESC
    LIMIT 20
""", (user["id"],))
history = cursor.fetchall()
conn.close()

if history:
    for alert in history:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
        with col1:
            st.markdown(f"**{alert['symbol']}**")
        with col2:
            st.markdown(f"{alert['condition']} ${alert['price']:,.2f}")
        with col3:
            st.caption(alert["created_at"][:16])
        with col4:
            st.caption("✅ Сработал")
        st.divider()
else:
    st.caption("Нет истории")