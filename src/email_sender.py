"""
Модуль отправки email через yagmail и Gmail API.
"""
import yagmail
import os
import pickle
import base64
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage

load_dotenv()

# Настройки почты для yagmail (сброс пароля)
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")  # Пароль приложения!

# Настройки Gmail API (для алертов)
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = '/var/www/crypto-is/credentials.json'
TOKEN_FILE = '/var/www/crypto-is/token.pickle'

# ============================================
# YAGMAIL (для сброса пароля)
# ============================================

def send_reset_code(to_email: str, code: str) -> bool:
    """
    Отправка кода сброса пароля на email через yagmail.
    """
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print("❌ Gmail не настроен в .env файле")
        return False
    
    try:
        yag = yagmail.SMTP(GMAIL_USER, GMAIL_PASSWORD)
        
        subject = "🔐 Crypto IS - Восстановление пароля"
        contents = f"""
        <h2>Восстановление пароля в Crypto IS</h2>
        <p>Вы запросили сброс пароля.</p>
        <p>Ваш код подтверждения: <b style="font-size: 24px;">{code}</b></p>
        <p>Код действителен в течение 15 минут.</p>
        <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
        <hr>
        <p style="color: #666;">© 2026 Crypto IS</p>
        """
        
        yag.send(to=to_email, subject=subject, contents=contents)
        print(f"✅ Код отправлен на {to_email}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки email (yagmail): {e}")
        return False

# ============================================
# GMAIL API (для ценовых алертов)
# ============================================

def get_gmail_service():
    """Получить авторизованный сервис Gmail API"""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
            print("\n✅ Авторизация Gmail API завершена!")
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def send_alert_email(to_email: str, symbol: str, condition: str, target_price: float, current_price: float) -> bool:
    """
    Отправка ценового алерта через Gmail API
    """
    if not to_email:
        return False
    
    try:
        service = get_gmail_service()
        
        condition_ru = "выше" if condition == "above" else "ниже"
        
        subject = f"🔔 Ценовой алерт: {symbol} {condition_ru} ${target_price:,.2f}"
        
        body = f"""
🚨 ЦЕНОВОЙ АЛЕРТ!

Актив: {symbol}
Условие: цена {condition_ru} ${target_price:,.2f}
Текущая цена: ${current_price:,.2f}

Время: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Crypto IS — Система мониторинга финансов
        """
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        service.users().messages().send(
            userId='me',
            body={'raw': encoded_message}
        ).execute()
        
        print(f"✅ Алерт отправлен на {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки алерта: {e}")
        return False


def test_email_api():
    """Тестовая отправка через Gmail API"""
    print("\n📧 Тест отправки email через Gmail API")
    test_email = input("Введите ваш email для теста: ").strip()
    
    success = send_alert_email(
        to_email=test_email,
        symbol="BTC",
        condition="above",
        target_price=50000,
        current_price=65000
    )
    
    if success:
        print("✅ Проверьте почту (возможно в спаме)!")
    else:
        print("❌ Ошибка. Проверьте настройтели.")


if __name__ == "__main__":
    test_email_api()