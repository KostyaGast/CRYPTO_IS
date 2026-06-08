"""
Фоновый процесс для проверки цен и отправки уведомлений
"""
import time
import threading
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, deactivate_alert
from fetcher import CryptoFetcher
from stock_fetcher import StockFetcher
from config import config


def get_current_price_for_symbol(symbol: str) -> float:
    """Получить текущую цену актива (крипта или акция)"""
    
    # 1. Проверяем криптовалюты
    for name, coin_id in config.SUPPORTED_COINS.items():
        if symbol.upper() in name.upper() or coin_id == symbol.lower():
            try:
                fetcher = CryptoFetcher(coin_id)
                return fetcher.get_current_price()
            except:
                return None
    
    # 2. Пробуем как акцию
    try:
        fetcher = StockFetcher(symbol)
        data = fetcher.get_data()
        if not data.empty:
            return data['close'].iloc[-1]
    except:
        pass
    
    return None


def send_telegram_alert(chat_id: str, symbol: str, condition: str, target_price: float, current_price: float):
    """Отправить уведомление в Telegram"""
    if not chat_id:
        return
    
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        return
    
    condition_ru = "выше" if condition == "above" else "ниже"
    emoji = "🟢" if condition == "above" else "🔴"
    
    message = f"""
{emoji} <b>ЦЕНОВОЙ АЛЕРТ!</b>

Актив: <b>{symbol}</b>
Условие: цена {condition_ru} ${target_price:,.2f}
Текущая цена: <b>${current_price:,.2f}</b>

🕐 {datetime.now().strftime('%H:%M:%S')}
    """
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
    except:
        pass


def send_email_alert(email: str, symbol: str, condition: str, target_price: float, current_price: float):
    """Отправить уведомление на email"""
    if not email:
        return
    
    try:
        import yagmail
        from dotenv import load_dotenv
        
        load_dotenv()
        
        gmail_user = os.getenv("GMAIL_USER")
        gmail_pass = os.getenv("GMAIL_PASSWORD")
        
        if not gmail_user or not gmail_pass:
            return
        
        yag = yagmail.SMTP(gmail_user, gmail_pass)
        
        condition_ru = "выше" if condition == "above" else "ниже"
        
        subject = f"🔔 Ценовой алерт: {symbol} {condition_ru} ${target_price:,.2f}"
        contents = f"""
        <h2>🔔 Ценовой алерт сработал!</h2>
        <p><b>Актив:</b> {symbol}</p>
        <p><b>Условие:</b> цена {condition_ru} ${target_price:,.2f}</p>
        <p><b>Текущая цена:</b> ${current_price:,.2f}</p>
        <p><b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        yag.send(to=email, subject=subject, contents=contents)
    except Exception as e:
        print(f"Email error: {e}")


def check_all_alerts():
    """Проверка всех активных алертов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем все активные алерты
    cursor.execute("""
        SELECT pa.*, u.username, u.email, u.telegram_chat_id 
        FROM price_alerts pa
        JOIN users u ON pa.user_id = u.id
        WHERE pa.active = 1
    """)
    alerts = cursor.fetchall()
    conn.close()
    
    triggered = []
    for alert in alerts:
        # Получаем текущую цену
        current_price = get_current_price_for_symbol(alert["symbol"])
        
        if current_price is None:
            continue
        
        # Проверяем условие
        condition_met = False
        if alert["condition"] == "above" and current_price >= alert["price"]:
            condition_met = True
        elif alert["condition"] == "below" and current_price <= alert["price"]:
            condition_met = True
        
        if condition_met:
            triggered.append({
                "alert_id": alert["id"],
                "user_id": alert["user_id"],
                "username": alert["username"],
                "email": alert["email"],
                "telegram_chat_id": alert["telegram_chat_id"],
                "symbol": alert["symbol"],
                "condition": alert["condition"],
                "target_price": alert["price"],
                "current_price": current_price
            })
    
    return triggered


def deactivate_alert(alert_id: int, user_id: int):
    """Деактивировать алерт"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE price_alerts SET active = 0 WHERE id = ? AND user_id = ?",
        (alert_id, user_id)
    )
    conn.commit()
    conn.close()


def check_alerts_loop():
    """Основной цикл проверки алертов"""
    print("🔄 Запущен фоновый мониторинг алертов...")
    
    while True:
        try:
            triggered = check_all_alerts()
            
            for alert in triggered:
                print(f"🔔 Сработал алерт: {alert['symbol']} -> ${alert['current_price']:,.2f}")
                
                # Отправляем в Telegram
                if alert.get("telegram_chat_id"):
                    send_telegram_alert(
                        alert["telegram_chat_id"],
                        alert["symbol"],
                        alert["condition"],
                        alert["target_price"],
                        alert["current_price"]
                    )
                
                # Отправляем на Email
                if alert.get("email"):
                    send_email_alert(
                        alert["email"],
                        alert["symbol"],
                        alert["condition"],
                        alert["target_price"],
                        alert["current_price"]
                    )
                
                # Деактивируем сработавший алерт
                deactivate_alert(alert["alert_id"], alert["user_id"])
            
            # Ждём 60 секунд перед следующей проверкой
            time.sleep(60)
            
        except Exception as e:
            print(f"Ошибка в мониторинге: {e}")
            time.sleep(60)


def start_alerts_monitoring():
    """Запускает мониторинг алертов в отдельном потоке"""
    thread = threading.Thread(target=check_alerts_loop, daemon=True)
    thread.start()
    print("✅ Мониторинг алертов запущен")