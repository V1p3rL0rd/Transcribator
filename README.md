# 🎙️ Transcribator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/faster--whisper-CTranslate2-2563EB?style=for-the-badge&logo=openai&logoColor=white" alt="faster-whisper">
  <img src="https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-475569?style=for-the-badge" alt="Cross-Platform">
</p>

> **Transcribator** — современное приватное веб-приложение для локальной транскрибации речи и видео (файлы, микрофон, YouTube, VK, Facebook) в текст и документы `.DOCX` на базе **Python**, **FastAPI** и оптимизированной библиотеки **faster-whisper** (CTranslate2).

Работает на 100% автономно на вашем компьютере: аудио и видео файлы никуда не отправляются в облако, обеспечивая полную конфиденциальность данных.

---

## ✨ Возможности

- 🚀 **Высокая скорость (faster-whisper)**: до 4x быстрее оригинального Whisper от OpenAI при том же качестве и меньшем потреблении оперативной памяти.
- 🔗 **Транскрибация по ссылке (YouTube, VK, Rutube, Facebook и др.)**: автоматическое извлечение и скачивание чистого аудиопотока через `yt-dlp` без необходимости загружать само видео на диск вручную.
- 💻 **Аппаратное ускорение**: автоматическое переключение между **NVIDIA GPU (CUDA)** и оптимизированным режимом **CPU (`int8`)** (включая Apple Silicon Mac M1/M2/M3/M4 и x86-64).
- 🎙️ **Запись с микрофона**: возможность надиктовать текст прямо в браузере без сторонних программ.
- 📁 **Широкая поддержка форматов**: MP3, WAV, M4A, OGG, WEBM, FLAC, AAC, MP4, MOV, MKV, OPUS.
- 🌐 **Мультиязычность**: автоматическое определение языка (русский, английский, украинский, казахский, немецкий и др.) с вероятностью распознавания.
- 🔄 **Режим перевода**: перевод любой речи на английский язык (`task="translate"`).
- ⏱️ **Интерактивные таймкоды**: клик по временной метке сегмента автоматически перематывает плеер к нужной секунде аудио.
- 🔍 **Поиск по транскрипции**: фильтрация и подсветка найденных слов в реальном времени.
- 💾 **Экспорт в удобных форматах**:
  - `.DOCX` — полноценный документ Microsoft Word с красивым заголовком, метаданными и абзацами;
  - `.TXT` — чистый текст для быстрой вставки.
- 📊 **Индикатор прогресса**: отслеживание хода распознавания в реальном времени.
- 📖 **Интерактивная документация API**: Swagger UI на `/docs` и ReDoc на `/redoc`.

---

## 🏗️ Архитектура проекта

```text
Transcribator/
├── app/
│   ├── __init__.py          # Пакет приложения
│   ├── main.py              # FastAPI сервер, эндпоинты API и маршруты статики
│   ├── models.py            # Pydantic-схемы данных (задачи, сегменты, результаты)
│   ├── tasks.py             # Асинхронный TaskManager (фоновая обработка задач)
│   ├── transcriber.py       # Движок faster-whisper, кэширование моделей
│   └── static/
│       └── index.html       # Адаптивный веб-интерфейс (Tailwind CSS, FontAwesome)
├── uploads/                 # Временная папка для загрузок (автоочистка)
├── requirements.txt         # Зависимости Python
├── run.py                   # Точка входа для запуска веб-сервера
├── start_unix.sh            # Скрипт быстрого запуска для macOS / Linux
└── README.md                # Документация проекта
```

---

## 🚀 Быстрый старт

Откройте терминал (**Командная строка CMD / PowerShell / Terminal**) в папке проекта и выполните всего 2 команды:

```bash
pip install -r requirements.txt
python run.py
```

После старта веб-интерфейс автоматически доступен по адресу:  
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (документация API: `/docs`)

---

## 💻 Пошаговая инструкция по платформам

### 1. Windows

1. Установите **Python 3.10–3.14** с [python.org](https://www.python.org/downloads/) *(обязательно отметьте галочку **"Add python.exe to PATH"** при установке)*.
2. Откройте командную строку (**CMD**) или **PowerShell** в папке проекта:
   ```cmd
   pip install -r requirements.txt
   python run.py
   ```
3. *(Опционально)*: Установите FFmpeg в PowerShell:
   ```powershell
   winget install Gyan.FFmpeg
   ```
4. *(Опционально для видеокарт NVIDIA)*:
   ```cmd
   pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
   ```

---

### 2. macOS

1. Установите Python и FFmpeg через Homebrew (если еще не установлены):
   ```bash
   brew install python ffmpeg
   ```
2. Откройте терминал в папке проекта:
   ```bash
   pip install -r requirements.txt
   python3 run.py
   ```
   *(либо выполните `./start_unix.sh`)*.

---

### 3. Ubuntu / Debian

1. Установите системные пакеты:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip ffmpeg git
   ```
2. Откройте терминал в папке проекта:
   ```bash
   pip install -r requirements.txt
   python3 run.py
   ```
3. *(Опционально для видеокарт NVIDIA)*: убедитесь, что установлены драйверы NVIDIA и выполните `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`.

---

После старта веб-интерфейс доступен по адресу:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (документация: `/docs`)

---

## ⚙️ Переменные окружения

Вы можете настраивать запуск через переменные среды:

| Переменная | По умолчанию | Описание |
| :--- | :--- | :--- |
| `PORT` | `8000` | Порт веб-сервера |
| `HOST` | `127.0.0.1` | Хост для биндинга (`0.0.0.0` для доступа по локальной сети) |
| `WHISPER_DEVICE` | `cuda` (если доступен), иначе `cpu` | Устройство для вычислений (`cpu`, `cuda`) |
| `WHISPER_COMPUTE_TYPE` | `float16` (для CUDA), `int8` (для CPU) | Точность квантования (`int8`, `float16`, `float32`) |
| `WHISPER_THREADS` | `4` | Количество потоков процессора для расчётов на CPU |

Пример запуска для локальной сети на GPU:
```bash
HOST=0.0.0.0 PORT=8080 WHISPER_DEVICE=cuda WHISPER_COMPUTE_TYPE=float16 python run.py
```

---

## 🔌 API Эндпоинты

- `GET /` — Главная страница веб-приложения.
- `GET /api/health` — Проверка состояния сервиса и информация об аппаратном ускорителе.
- `GET /api/models` — Список доступных моделей Whisper (`tiny`, `base`, `small`, `medium`, `large-v3`).
- `POST /api/transcribe` — Загрузка файла и запуск асинхронной задачи (принимает `file`, `model_size`, `language`, `task`, `initial_prompt`, `condition_on_previous_text`).
- `POST /api/transcribe-url` — Скачивание аудио по ссылке (YouTube, VK, Facebook, Rutube, TikTok и др.) и запуск расшифровки.
- `GET /api/tasks/{task_id}` — Получение статуса, прогресса (0-100%) и результата транскрибации.
- `GET /api/export/{task_id}/{format}` — Скачивание результата в формате `txt`, `srt`, `vtt`, `json`.

---

## 🧠 Доступные модели Whisper

| Модель | Размер | Скорость | Рекомендуемое применение |
| :--- | :--- | :--- | :--- |
| **small** | ~244 MB | ~6x | **Рекомендуется для CPU**: отличная точность для разговорной речи, диалогов и терминов |
| **large-v3-turbo** | ~800 MB | ~8x | **Флагманское качество**: точность Large-v3 при высокой скорости, отлично распознает сленг и акценты |
| **base** | ~74 MB | ~16x | Базовый черновик для четкой и медленной речи |
| **tiny** | ~39 MB | ~32x | Сверхбыстрый черновик |
| **medium** | ~769 MB | ~2x | Высокая точность для сложных аудиозаписей |
| **large-v3**| ~1.5 GB | ~1x | Студийное качество, идеальная пунктуация и распознавание |

*Модель скачивается автоматически из Hugging Face при первом обращении и кэшируется локально.*
