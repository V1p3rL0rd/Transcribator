@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Transcribator

rem 1. Check Python
set PY=python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ====================================================
        echo  [ERROR] Python is not installed or not in PATH!
        echo ====================================================
        echo.
        echo Please install Python 3.10-3.14 from:
        echo https://www.python.org/downloads/
        echo.
        echo IMPORTANT: Check the box "Add python.exe to PATH" during installation!
        echo.
        pause
        exit /b 1
    ) else (
        set PY=py
    )
)

rem 2. First-time setup: check dependencies
%PY% -c "import uvicorn, faster_whisper, docx, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo ====================================================
    echo        Transcribator: First-Time Setup
    echo ====================================================
    echo.
    echo Installing required libraries. This may take a few minutes...
    echo.
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

rem 3. Launch browser and application
echo.
echo ====================================================
echo        Starting Transcribator Web App
echo ====================================================
echo Web UI: http://127.0.0.1:8000
echo.

start "" http://127.0.0.1:8000
%PY% run.py

if errorlevel 1 (
    echo.
    echo Application stopped with an error.
    pause
)
