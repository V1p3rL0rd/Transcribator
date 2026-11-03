@echo off
chcp 65001 > nul
title Transcribator — Запуск приложения

echo ====================================================
echo        Запуск Transcribator для Windows
echo ====================================================
echo.

:: 1. Проверка наличия Python
set PY_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ОШИБКА] Python не найден в системе!
        echo Установите Python 3.10-3.12 с официального сайта: https://www.python.org/downloads/
        echo ОБЯЗАТЕЛЬНО отметьте галочку "Add python.exe to PATH" при установке.
        echo.
        pause
        exit /b
    ) else (
        set PY_CMD=py
    )
)

:: 2. Создание виртуального окружения (если еще нет)
if not exist ".venv" (
    echo [1/3] Создание виртуального окружения (.venv)...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать .venv
        pause
        exit /b
    )
)

:: 3. Установка библиотек напрямую через python в .venv
echo [2/3] Проверка и установка зависимостей...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 4. Запуск приложения и открытие браузера
echo.
echo [3/3] Запуск веб-сервера Transcribator...
echo Сервер будет доступен по адресу: http://127.0.0.1:8000
echo.

start "" http://127.0.0.1:8000
.venv\Scripts\python.exe run.py

pause
