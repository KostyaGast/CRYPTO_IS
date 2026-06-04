"""
Модуль работы с базой данных SQLite.
Хранение пользователей, сброс пароля, привязка Яндекс ID.
"""
import sqlite3
import hashlib
import random
import string
import pandas as pd  
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict

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
            yandex_id TEXT UNIQUE,
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
    
    # Проверяем наличие колонок (для старых версий)
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'email' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if 'yandex_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN yandex_id TEXT")
    
    # Таблица для баланса (ДОБАВЛЯЕМ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            balance REAL DEFAULT 1000000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Хеширование пароля SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str, email: str = "") -> Tuple[bool, str]:
    """Регистрация нового пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Пользователь с таким логином уже существует"
    
    if email and email.strip():
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "❌ Этот email уже зарегистрирован"
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email if email else None)
        )
        user_id = cursor.lastrowid
        
        # Создаем начальный баланс
        cursor.execute(
            "INSERT INTO user_balance (user_id, balance) VALUES (?, ?)",
            (user_id, 1000000.0)
        )
        
        conn.commit()
        return True, "✅ Регистрация успешна!"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def login_user(username: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """Вход пользователя по логину или email."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username, username)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "❌ Пользователь не найден", None
    
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
        "yandex_id": user["yandex_id"],
        "created_at": user["created_at"]
    }
    
    return True, "✅ Вход выполнен", user_data

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Получение пользователя по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "yandex_id": user["yandex_id"],
            "created_at": user["created_at"]
        }
    return None

def get_user_by_yandex_id(yandex_id: str) -> Optional[dict]:
    """Ищет пользователя по Яндекс ID."""
    if not yandex_id:
        return None
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE yandex_id = ?", (yandex_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "yandex_id": user["yandex_id"]
        }
    return None

def create_user_from_yandex(yandex_id: str, username: str, email: str) -> Tuple[bool, str, Optional[int]]:
    """Создаёт нового пользователя на основе данных Яндекса."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Генерируем уникальный логин
    base_username = username.replace(" ", "_").lower()
    final_username = base_username
    counter = 1
    
    while True:
        cursor.execute("SELECT id FROM users WHERE username = ?", (final_username,))
        if not cursor.fetchone():
            break
        final_username = f"{base_username}_{counter}"
        counter += 1
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, yandex_id, password_hash) VALUES (?, ?, ?, '')",
            (final_username, email, yandex_id)
        )
        user_id = cursor.lastrowid
        
        # Создаем начальный баланс
        cursor.execute(
            "INSERT INTO user_balance (user_id, balance) VALUES (?, ?)",
            (user_id, 1000000.0)
        )
        
        conn.commit()
        return True, "✅ Аккаунт создан", user_id
    except Exception as e:
        return False, f"❌ Ошибка: {e}", None
    finally:
        conn.close()

def link_yandex_to_user(user_id: int, yandex_id: str, yandex_email: str = "") -> Tuple[bool, str]:
    """Привязывает Яндекс ID к существующему пользователю."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, не привязан ли этот Яндекс ID к другому пользователю
    cursor.execute("SELECT id FROM users WHERE yandex_id = ? AND id != ?", (yandex_id, user_id))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Этот Яндекс ID уже привязан к другому аккаунту"
    
    try:
        cursor.execute(
            "UPDATE users SET yandex_id = ?, email = COALESCE(NULLIF(email, ''), ?) WHERE id = ?",
            (yandex_id, yandex_email, user_id)
        )
        conn.commit()
        return True, "✅ Яндекс ID успешно привязан"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def update_user_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Обновление пароля пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        conn.commit()
        return True, "✅ Пароль успешно изменён"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

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
        return {"id": user["id"], "username": user["username"], "email": user["email"]}
    return None

def get_user_by_username(username: str) -> Optional[dict]:
    """Поиск пользователя по username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {"id": user["id"], "username": user["username"], "email": user["email"]}
    return None

def generate_reset_code() -> str:
    """Генерация 6-значного кода."""
    return ''.join(random.choices(string.digits, k=6))

def create_password_reset(email_or_username: str) -> Tuple[bool, str, Optional[str]]:
    """Создание запроса на сброс пароля."""
    user = get_user_by_email(email_or_username)
    if not user:
        user = get_user_by_username(email_or_username)
    
    if not user:
        return False, "❌ Пользователь с таким email или логином не найден", None
    
    if not user.get("email"):
        return False, "❌ У этого аккаунта не указан email для восстановления", None
    
    reset_code = generate_reset_code()
    expires_at = datetime.now() + timedelta(minutes=15)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM password_reset WHERE user_id = ?", (user["id"],))
    cursor.execute(
        "INSERT INTO password_reset (user_id, reset_code, expires_at) VALUES (?, ?, ?)",
        (user["id"], reset_code, expires_at)
    )
    conn.commit()
    conn.close()
    
    return True, f"📧 Код сброса отправлен на {user['email']}", user["email"]

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
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        cursor.execute("UPDATE password_reset SET used = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, "✅ Пароль успешно изменён"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def update_user_email(user_id: int, new_email: str) -> Tuple[bool, str]:
    """Обновление email пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, user_id))
    if cursor.fetchone():
        conn.close()
        return False, "❌ Этот email уже используется"
    
    try:
        cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
        conn.commit()
        return True, "✅ Email обновлён"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"
    finally:
        conn.close()

def unlink_yandex(user_id: int) -> bool:
    """Отвязывает Яндекс ID от пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET yandex_id = NULL WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def delete_user(user_id: int) -> bool:
    """Удаляет пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM password_reset WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_balance WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def add_telegram_column():
    """Добавляет колонки для Telegram."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, существует ли таблица users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        conn.close()
        return  # Таблицы нет — выходим

    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'telegram_chat_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN telegram_chat_id TEXT")
    if 'telegram_verified' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN telegram_verified INTEGER DEFAULT 0")
    if 'telegram_code' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN telegram_code TEXT")
    
    conn.commit()
    conn.close()

def generate_telegram_code(user_id: int) -> str:
    """Генерирует код для привязки Telegram."""
    import random
    code = ''.join(random.choices('0123456789', k=6))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET telegram_code = ? WHERE id = ?", (code, user_id))
    conn.commit()
    conn.close()
    
    return code

def verify_telegram(chat_id: str, code: str) -> Tuple[bool, str]:
    """Проверяет код и привязывает Telegram."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username FROM users WHERE telegram_code = ?",
        (code,)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "❌ Неверный код"
    
    cursor.execute(
        "UPDATE users SET telegram_chat_id = ?, telegram_verified = 1, telegram_code = NULL WHERE id = ?",
        (chat_id, user["id"])
    )
    conn.commit()
    conn.close()
    
    return True, f"✅ Telegram привязан к аккаунту {user['username']}"

def unlink_telegram(user_id: int) -> bool:
    """Отвязывает Telegram от пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET telegram_chat_id = NULL, telegram_verified = 0 WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()
    return True

def get_telegram_chat_id(user_id: int) -> Optional[str]:
    """Получает chat_id пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_chat_id FROM users WHERE id = ? AND telegram_verified = 1", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["telegram_chat_id"] if result else None

def bulk_save_crypto_history(data: List[Dict]):
    """Массовое сохранение истории криптовалют."""
    conn = get_connection()
    cursor = conn.cursor()
    for item in data:
        cursor.execute("""
            INSERT OR IGNORE INTO crypto_history (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item['symbol'], item['date'], item['open'], item['high'], item['low'], item['close'], item['volume']))
    conn.commit()
    conn.close()

def bulk_save_stock_history(data: List[Dict]):
    """Массовое сохранение истории акций."""
    conn = get_connection()
    cursor = conn.cursor()
    for item in data:
        cursor.execute("""
            INSERT OR IGNORE INTO stock_history (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item['symbol'], item['date'], item['open'], item['high'], item['low'], item['close'], item['volume']))
    conn.commit()
    conn.close()

def get_available_crypto_symbols() -> List[str]:
    """Возвращает список криптовалют, по которым есть данные."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT symbol FROM crypto_history ORDER BY symbol")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_available_stock_symbols() -> List[str]:
    """Возвращает список акций, по которым есть данные."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT symbol FROM stock_history ORDER BY symbol")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def get_crypto_date_range(symbol: str) -> tuple:
    """Возвращает диапазон дат для криптовалюты."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MIN(date), MAX(date), COUNT(*) FROM crypto_history WHERE symbol = ?",
        (symbol,)
    )
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        return result[0], result[1], result[2]
    return None, None, 0

def get_stock_date_range(symbol: str) -> tuple:
    """Возвращает диапазон дат для акции."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MIN(date), MAX(date), COUNT(*) FROM stock_history WHERE symbol = ?",
        (symbol,)
    )
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None, 0)

def init_history_tables():
    """Создаёт таблицы для хранения истории."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            UNIQUE(symbol, date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            UNIQUE(symbol, date)
        )
    """)
    
    conn.commit()
    conn.close()

def get_crypto_history(symbol: str, months: int = 1) -> pd.DataFrame:
    """Получает историю криптовалюты за указанное количество месяцев."""
    import pandas as pd
    from datetime import datetime, timedelta
    
    conn = get_connection()
    
    # Берём ВСЕ данные по символу
    query = "SELECT * FROM crypto_history WHERE symbol = ? ORDER BY date ASC"
    df = pd.read_sql_query(query, conn, params=(symbol,))
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
    
    # Фильтруем по дате
    df['date'] = pd.to_datetime(df['date'])
    cutoff = datetime.now() - timedelta(days=months * 30)
    df = df[df['date'] >= cutoff]
    
    return df

def get_stock_history(symbol: str, months: int = 1) -> pd.DataFrame:
    """Получает историю акции за указанное количество месяцев."""
    import pandas as pd
    from datetime import datetime, timedelta
    
    conn = get_connection()
    query = "SELECT * FROM stock_history WHERE symbol = ? ORDER BY date ASC"
    df = pd.read_sql_query(query, conn, params=(symbol,))
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
    
    df['date'] = pd.to_datetime(df['date'])
    cutoff = datetime.now() - timedelta(days=months * 30)
    df = df[df['date'] >= cutoff]
    
    return df

# НОВЫЕ ФУНКЦИИ ДЛЯ ТЕРМИНАЛА
def update_balance(user_id: int, new_balance: float) -> bool:
    """Обновляет баланс пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE user_balance 
            SET balance = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (new_balance, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating balance: {e}")
        return False
    finally:
        conn.close()

def init_trading_tables():
    """Создаёт таблицы для трейдинга."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            order_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, symbol)
        )
    """)
    conn.commit()
    conn.close()

def place_order(user_id: int, symbol: str, asset_type: str, price: float, quantity: float, order_type: str):
    """Совершает сделку и обновляет портфель и баланс."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Начинаем транзакцию
        cursor.execute("BEGIN TRANSACTION")
        
        # Получаем текущий баланс
        current_balance = get_balance(user_id)
        amount = price * quantity
        
        if order_type == 'buy':
            if current_balance < amount:
                raise Exception("Insufficient funds")
            new_balance = current_balance - amount
        else:  # sell
            new_balance = current_balance + amount
        
        # Обновляем баланс
        update_balance(user_id, new_balance)
        
        # Записываем сделку
        cursor.execute(
            "INSERT INTO orders (user_id, symbol, asset_type, price, quantity, order_type) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, symbol, asset_type, price, quantity, order_type)
        )
        
        # Обновляем портфель
        cursor.execute("SELECT * FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
        row = cursor.fetchone()
        
        if row:
            old_qty = row["quantity"]
            old_avg = row["avg_price"]
            if order_type == "buy":
                new_qty = old_qty + quantity
                new_avg = ((old_avg * old_qty) + (price * quantity)) / new_qty
                cursor.execute(
                    "UPDATE holdings SET quantity = ?, avg_price = ? WHERE user_id = ? AND symbol = ?",
                    (new_qty, new_avg, user_id, symbol)
                )
            else:  # sell
                new_qty = old_qty - quantity
                if new_qty <= 0:
                    cursor.execute("DELETE FROM holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
                else:
                    cursor.execute(
                        "UPDATE holdings SET quantity = ? WHERE user_id = ? AND symbol = ?",
                        (new_qty, user_id, symbol)
                    )
        else:
            if order_type == "buy":
                cursor.execute(
                    "INSERT INTO holdings (user_id, symbol, quantity, avg_price) VALUES (?, ?, ?, ?)",
                    (user_id, symbol, quantity, price)
                )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_portfolio(user_id: int):
    """Возвращает портфель пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holdings WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_orders(user_id: int, limit: int = 50):
    """Возвращает историю сделок."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_balance(user_id: int) -> float:
    """Возвращает текущий баланс пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM user_balance WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result["balance"]
    else:
        # Если записи нет, создаем с начальным балансом
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_balance (user_id, balance) VALUES (?, ?)",
            (user_id, 1000000.0)
        )
        conn.commit()
        conn.close()
        return 1000000.0

# Инициализация
init_history_tables()
init_trading_tables()
init_database()
add_telegram_column()