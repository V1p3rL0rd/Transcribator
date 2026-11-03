@echo off
cd /d "%~dp0"
title Transcribator

echo ====================================================
echo             Transcribator Launcher
echo ====================================================
echo.

echo [1/2] Checking and installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

echo.
echo [2/2] Starting Transcribator web server...
echo Web UI will open at: http://127.0.0.1:8000
echo.

start "" http://127.0.0.1:8000
python run.py

pause
