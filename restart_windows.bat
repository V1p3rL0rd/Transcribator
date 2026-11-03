@echo off
chcp 65001 > nul
title Transcribator — Перезапуск

echo ====================================================
echo        Перезапуск Transcribator (Windows)
echo ====================================================
echo.

echo [1/2] Завершение предыдущих процессов Python...
taskkill /F /IM python.exe >nul 2>&1

echo [2/2] Запуск сервера...
call .venv\Scripts\activate.bat
start "" http://127.0.0.1:8000
python run.py

pause
