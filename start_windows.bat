@echo off
setlocal
cd /d "%~dp0"
title Transcribator

rem Run PowerShell with Bypass policy so it works regardless of Windows security settings
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_windows.ps1"

if %errorlevel% neq 0 (
    echo.
    pause
)
