# Transcribator - Скрипт запуска для Windows PowerShell
$ErrorActionPreference = "Stop"

# Переход в папку со скриптом (гарантирует правильный каталог даже при запуске от Администратора)
Set-Location -LiteralPath $PSScriptRoot

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "        Запуск Transcribator для Windows" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Поиск рабочего Python
$pythonCmd = $null

try {
    $ver = & python -c "import sys; print(sys.version)" 2>$null
    if ($ver) { $pythonCmd = "python" }
} catch {}

if (-not $pythonCmd) {
    try {
        $ver = & py -c "import sys; print(sys.version)" 2>$null
        if ($ver) { $pythonCmd = "py" }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "[ОШИБКА] Python не найден или открывает Microsoft Store!" -ForegroundColor Red
    Write-Host "1. Установите Python 3.10-3.12: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "2. ОБЯЗАТЕЛЬНО отметьте галочку 'Add python.exe to PATH' при установке." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Нажмите Enter для выхода..."
    exit 1
}

# 2. Создание виртуального окружения (.venv)
if (-not (Test-Path ".venv")) {
    Write-Host "[1/3] Создание виртуального окружения (.venv)..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ОШИБКА] Не удалось создать .venv!" -ForegroundColor Red
        Read-Host "Нажмите Enter для выхода..."
        exit 1
    }
}

# 3. Установка зависимостей напрямую через python.exe внутри .venv
Write-Host "[2/3] Проверка и установка зависимостей..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ОШИБКА] Ошибка при установке зависимостей!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода..."
    exit 1
}

# 4. Запуск веб-сервера и браузера
Write-Host ""
Write-Host "[3/3] Запуск веб-сервера Transcribator..." -ForegroundColor Green
Write-Host "Сервер доступен по адресу: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""

Start-Process "http://127.0.0.1:8000"
& .\.venv\Scripts\python.exe run.py
