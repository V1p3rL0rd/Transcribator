#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "===================================================="
echo "        Запуск Transcribator (macOS / Linux)"
echo "===================================================="
echo ""

# 1. Проверка Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] python3 не найден в системе!"
    echo "Установите Python 3.10-3.12."
    exit 1
fi

# 2. Создание venv если нет
if [ ! -d ".venv" ]; then
    echo "[1/3] Создание виртуального окружения (.venv)..."
    python3 -m venv .venv
fi

# 3. Активация и установка зависимостей
echo "[2/3] Проверка и установка зависимостей..."
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 4. Запуск
echo ""
echo "[3/3] Запуск веб-сервера Transcribator..."
echo "Сервер доступен по адресу: http://127.0.0.1:8000"
echo ""

# Открытие браузера (macOS: open, Linux: xdg-open)
if command -v open &> /dev/null; then
    (sleep 1 && open http://127.0.0.1:8000) &
elif command -v xdg-open &> /dev/null; then
    (sleep 1 && xdg-open http://127.0.0.1:8000) &
fi

python run.py
