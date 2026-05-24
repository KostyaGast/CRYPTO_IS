#!/usr/bin/env python3
import sys
import os

# Добавляем пути для импорта
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Импортируем после добавления путей
from src.telegram_bot import start_polling

if __name__ == "__main__":
    print("🚀 Запуск Telegram бота...")
    start_polling()