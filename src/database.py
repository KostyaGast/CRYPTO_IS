"""
Модуль работы с базой данных SQLite.
Хранение пользователей, сброс пароля через email.
"""
import sqlite3
import hashlib
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crypto_is.db"

def get_connection():
    """Создание подключения к БД."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Создание таблиц, если их нет."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Таблица для сброса пароля
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reset_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Хеширование пароля SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str, email: str = "") -> Tuple[bool, str]:
    """
    Регистрация нового пользователя.
    Проверяет уникальность username и email.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверка уникальности username
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Пользователь с таким логином уже существует"
    
    # Проверка уникальности email (если указан)
    if email and email.strip():
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "❌ Этот email уже зарегистрирован"
    if not email or email.strip() == "":
        return False, "❌ Email обязателен для регистрации"
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email if email else None)
        )
        conn.commit()
        return True, "✅ Регистрация успешна!"
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: users.email" in str(e):
            return False, "❌ Этот email уже зарегистрирован"
        elif "UNIQUE constraint failed: users.username" in str(e):
            return False, "❌ Пользователь с таким логином уже существует"
        return False, f"❌ Ошибка: {e}"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def login_user(login: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Вход пользователя по логину ИЛИ email.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ищем пользователя по логину ИЛИ email
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (login, login)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "❌ Пользователь с таким логином или email не найден", None
    
    password_hash = hash_password(password)
    if user["password_hash"] != password_hash:
        conn.close()
        return False, "❌ Неверный пароль", None
    
    cursor.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
        (user["id"],)
    )
    conn.commit()
    conn.close()
    
    user_data = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"]
    }
    
    return True, "✅ Вход выполнен", user_data

def get_user_by_email(email: str) -> Optional[dict]:
    """Поиск пользователя по email."""
    if not email:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    return None

def get_user_by_username(username: str) -> Optional[dict]:
    """Поиск пользователя по username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    return None

def is_email_registered(email: str) -> bool:
    """Проверка, зарегистрирован ли email."""
    if not email:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def generate_reset_code() -> str:
    """Генерация 6-значного кода."""
    return ''.join(random.choices(string.digits, k=6))

def create_password_reset(email_or_username: str) -> Tuple[bool, str, Optional[str]]:
    """
    Создание запроса на сброс пароля.
    Возвращает (успех, сообщение, email_пользователя).
    """
    # Ищем пользователя
    user = get_user_by_email(email_or_username)
    if not user:
        user = get_user_by_username(email_or_username)
    
    if not user:
        return False, "❌ Пользователь с таким email или логином не найден", None
    
    if not user.get("email"):
        return False, "❌ У этого аккаунта не указан email для восстановления", None
    
    # Генерируем код
    reset_code = generate_reset_code()
    expires_at = datetime.now() + timedelta(minutes=15)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Удаляем старые коды
    cursor.execute("DELETE FROM password_reset WHERE user_id = ?", (user["id"],))
    
    # Создаём новый код
    cursor.execute(
        "INSERT INTO password_reset (user_id, reset_code, expires_at) VALUES (?, ?, ?)",
        (user["id"], reset_code, expires_at)
    )
    conn.commit()
    conn.close()
    
    # Отправляем код на email
    from email_sender import send_reset_code
    send_reset_code(user["email"], reset_code)
    
    return True, f"📧 Код отправлен на {user['email']}", user["email"]
def verify_reset_code(email: str, code: str) -> Tuple[bool, str, Optional[int]]:
    """Проверка кода сброса пароля."""
    user = get_user_by_email(email)
    if not user:
        return False, "❌ Пользователь не найден", None
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM password_reset 
        WHERE user_id = ? AND reset_code = ? AND used = 0 AND expires_at > ?
        ORDER BY id DESC LIMIT 1
    """, (user["id"], code, datetime.now()))
    
    reset_request = cursor.fetchone()
    conn.close()
    
    if not reset_request:
        return False, "❌ Неверный или истекший код", None
    
    return True, "✅ Код подтверждён", user["id"]

def reset_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Установка нового пароля."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        
        # Отмечаем код как использованный
        cursor.execute(
            "UPDATE password_reset SET used = 1 WHERE user_id = ?",
            (user_id,)
        )
        
        conn.commit()
        return True, "✅ Пароль успешно изменён!"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

# Инициализация БД
init_database()