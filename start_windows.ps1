# Transcribator - Скрипт запуска для Windows PowerShell
$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "        Запуск Transcribator для Windows" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Поиск Python (python или py)
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Host "[ОШИБКА] Python не найден в системе!" -ForegroundColor Red
    Write-Host "Скачайте Python 3.10-3.12 с официального сайта: https://www.python.org/downloads/"
    Write-Host "ОБЯЗАТЕЛЬНО отметьте галочку 'Add python.exe to PATH' при установке." -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода..."
    exit 1
}

# 2. Создание виртуального окружения (если еще нет)
if (-not (Test-Path ".venv")) {
    Write-Host "[1/3] Создание виртуального окружения (.venv)..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
}

# 3. Установка зависимостей напрямую через python.exe в .venv (без проблем с ExecutionPolicy)
Write-Host "[2/3] Проверка и установка зависимостей..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Запуск веб-сервера
Write-Host ""
Write-Host "[3/3] Запуск веб-сервера Transcribator..." -ForegroundColor Green
Write-Host "Сервер доступен по адресу: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""

Start-Process "http://127.0.0.1:8000"
& .\.venv\Scripts\python.exe run.py
