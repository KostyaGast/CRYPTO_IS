"""
Модуль отправки email через yagmail.
"""
import yagmail
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки почты (используйте свой Gmail)
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")  # Пароль приложения!

def send_reset_code(to_email: str, code: str) -> bool:
    """
    Отправка кода сброса пароля на email.
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
        print(f"❌ Ошибка отправки email: {e}")
        return False