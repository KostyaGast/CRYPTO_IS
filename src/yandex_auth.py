"""
Модуль авторизации через Яндекс ID.
"""
import streamlit as st
import requests
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://cryptois.abrdns.com/oauth2callback")


def get_yandex_auth_url() -> str:
    """Генерирует URL для входа через Яндекс."""
    params = {
        "response_type": "code",
        "client_id": YANDEX_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "login:email login:info",
        "state": "yandex"
    }
    return f"https://oauth.yandex.ru/authorize?{urllib.parse.urlencode(params)}"


def process_yandex_callback(code: str) -> dict:
    """Обменивает код на токен и получает данные пользователя."""
    token_url = "https://oauth.yandex.ru/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": YANDEX_CLIENT_ID,
        "client_secret": YANDEX_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()
    
    if "access_token" not in token_json:
        raise Exception(f"Ошибка получения токена: {token_json}")
    
    access_token = token_json["access_token"]
    
    user_url = "https://login.yandex.ru/info"
    headers = {"Authorization": f"OAuth {access_token}"}
    
    user_response = requests.get(user_url, headers=headers)
    user_data = user_response.json()
    
    return {
        "yandex_id": str(user_data.get("id", "")),
        "username": user_data.get("display_name", user_data.get("real_name", "Пользователь")),
        "email": user_data.get("default_email", ""),
        "avatar": f"https://avatars.yandex.net/get-yapic/{user_data.get('default_avatar_id', '0')}/islands-200"
    }


def handle_yandex_callback():
    """
    Проверяет наличие кода в URL и выполняет вход.
    """
    from database import get_user_by_yandex_id, create_user_from_yandex, link_yandex_to_user
    
    query_params = st.query_params
    
    if "code" in query_params:
        code = query_params["code"]
        
        with st.spinner("🔄 Выполняется вход через Яндекс..."):
            try:
                user_data = process_yandex_callback(code)
                yandex_id = user_data["yandex_id"]
                
                # Проверяем, не нужно ли привязать к существующему пользователю
                if "link_yandex_for" in st.session_state:
                    user_id = st.session_state["link_yandex_for"]
                    success, message = link_yandex_to_user(user_id, yandex_id, user_data["email"])
                    
                    if success:
                        del st.session_state["link_yandex_for"]
                        st.session_state["yandex_linked"] = True
                        st.success(message)
                    else:
                        st.error(message)
                    
                    st.query_params.clear()
                    st.switch_page("pages/profile.py")
                    return True
                
                # Ищем пользователя по yandex_id
                existing_user = get_user_by_yandex_id(yandex_id)
                
                if success:
                    from database import get_user_by_id
                    new_user = get_user_by_id(user_id)
                    st.session_state["authenticated"] = True
                    st.session_state["auth_method"] = "yandex"
                    st.session_state["user"] = new_user
                    
                    # ← ДОБАВИТЬ СОХРАНЕНИЕ ВХОДА
                    from pages.profile import save_login
                    save_login("***.***.***.***", "Web Browser")
                    
                    st.query_params.clear()
                    st.rerun()
                else:
                    # Новый пользователь — на страницу завершения регистрации
                    st.session_state["pending_yandex"] = {
                        "yandex_id": yandex_id,
                        "username": user_data["username"],
                        "email": user_data["email"],
                        "avatar": user_data["avatar"]
                    }
                    st.query_params.clear()
                    st.switch_page("pages/yandex_register.py")
                    
            except Exception as e:
                st.error(f"❌ Ошибка авторизации: {str(e)}")
    
    return False