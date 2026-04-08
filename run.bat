@echo off
chcp 65001 >nul
title Crypto IS - Запуск

echo ================================================
echo    CRYPTO IS - ИНФОРМАЦИОННАЯ СИСТЕМА
echo    BTC и ETH (только будние дни ПН-ПТ)
echo ================================================
echo.

cd /d "%~dp0"

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Скачайте Python с https://www.python.org/
    echo При установке поставьте галочку "Add Python to PATH"
    pause
    exit /b
)

echo [1/4] Python найден: 
python --version

:: Создание venv если нет
if not exist "venv\" (
    echo.
    echo [2/4] Создание виртуального окружения...
    python -m venv venv
) else (
    echo.
    echo [2/4] Виртуальное окружение уже существует
)

:: Активация
echo.
echo [3/4] Активация окружения и установка пакетов...
call venv\Scripts\activate.bat

:: Установка зависимостей
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

:: Запуск
echo.
echo [4/4] Запуск приложения...
echo.
echo ================================================
echo    ПРИЛОЖЕНИЕ ЗАПУЩЕНО!
echo    Откройте браузер и перейдите по адресу:
echo    http://localhost:8501
echo ================================================
echo.
echo Для остановки закройте это окно или нажмите Ctrl+C
echo.

streamlit run src/main.py

pause