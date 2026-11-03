import os
import uuid
import threading
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Optional

from app.models import TaskStatus, TranscriptionResult
from app.transcriber import transcriber_manager


class TaskManager:
    """Thread-safe task manager for asynchronous audio transcription."""

    def __init__(self):
        self._tasks: Dict[str, TaskStatus] = {}
        self._lock = threading.Lock()

    def create_task(self, filename: str, model_name: str) -> str:
        task_id = str(uuid.uuid4())
        task_status = TaskStatus(
            task_id=task_id,
            status="queued",
            progress=0,
            filename=filename,
            model_name=model_name,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._tasks[task_id] = task_status
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task_progress(self, task_id: str, progress: int):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = progress
                if self._tasks[task_id].status == "queued":
                    self._tasks[task_id].status = "processing"

    def complete_task(self, task_id: str, result: TranscriptionResult):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = "completed"
                self._tasks[task_id].progress = 100
                self._tasks[task_id].completed_at = datetime.now(timezone.utc).isoformat()
                self._tasks[task_id].result = result

    def fail_task(self, task_id: str, error_message: str):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = "failed"
                self._tasks[task_id].error = error_message
                self._tasks[task_id].completed_at = datetime.now(timezone.utc).isoformat()

    def run_transcription(
        self,
        task_id: str,
        file_path: str,
        filename: str,
        model_name: str,
        language: Optional[str] = None,
        task_type: str = "transcribe",
        initial_prompt: Optional[str] = None,
        condition_on_previous_text: bool = False,
    ):
        """Worker thread function."""
        try:
            self.update_task_progress(task_id, 5)

            def on_progress(pct: int):
                self.update_task_progress(task_id, pct)

            result = transcriber_manager.transcribe(
                audio_path=file_path,
                task_id=task_id,
                filename=filename,
                model_size=model_name,
                language=language,
                task=task_type,
                initial_prompt=initial_prompt,
                condition_on_previous_text=condition_on_previous_text,
                progress_callback=on_progress,
            )
            self.complete_task(task_id, result)
        except Exception as e:
            self.fail_task(task_id, str(e))
        finally:
            # Clean up uploaded audio file after transcription
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    def run_url_transcription(
        self,
        task_id: str,
        url: str,
        uploads_dir: str,
        model_name: str,
        language: Optional[str] = None,
        task_type: str = "transcribe",
        initial_prompt: Optional[str] = None,
        condition_on_previous_text: bool = False,
    ):
        """Worker thread function to download audio from URL and transcribe."""
        cache_dir = os.path.join(uploads_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        url_hash = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]
        meta_path = os.path.join(cache_dir, f"{url_hash}.json")

        audio_file = None
        title = "Video Audio"

        # Check if already cached from previous download
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    cached_file = meta.get("audio_file")
                    if cached_file and os.path.exists(cached_file) and os.path.getsize(cached_file) > 1000:
                        audio_file = cached_file
                        title = meta.get("title", title)
            except Exception:
                pass

        try:
            if not audio_file:
                import yt_dlp

                self.update_task_progress(task_id, 3)

                out_tmpl = os.path.join(cache_dir, f"{url_hash}.%(ext)s")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": out_tmpl,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    # Bypass YouTube "Sign in to confirm you're not a bot"
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["android", "ios", "web"]
                        }
                    },
                    "http_headers": {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/123.0.0.0 Safari/537.36"
                        )
                    },
                }

                cookie_browser = os.environ.get("YT_COOKIES_BROWSER")
                if cookie_browser:
                    ydl_opts["cookiesfrombrowser"] = (cookie_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "Video Audio")
                    for fname in os.listdir(cache_dir):
                        if fname.startswith(url_hash) and not fname.endswith(".json"):
                            audio_file = os.path.join(cache_dir, fname)
                            break

                if not audio_file or not os.path.exists(audio_file):
                    raise RuntimeError("Не удалось скачать звуковую дорожку по указанной ссылке.")

                # Save metadata for instant re-transcription with other models
                try:
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump({"title": title, "audio_file": audio_file}, f, ensure_ascii=False)
                except Exception:
                    pass

            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].filename = f"{title}"

            self.update_task_progress(task_id, 10)

            def on_progress(pct: int):
                scaled = 10 + int(pct * 0.9)
                self.update_task_progress(task_id, min(99, scaled))

            result = transcriber_manager.transcribe(
                audio_path=audio_file,
                task_id=task_id,
                filename=title,
                model_size=model_name,
                language=language,
                task=task_type,
                initial_prompt=initial_prompt,
                condition_on_previous_text=condition_on_previous_text,
                progress_callback=on_progress,
            )
            self.complete_task(task_id, result)
        except Exception as e:
            err_msg = str(e)
            if "Sign in to confirm you're not a bot" in err_msg:
                err_msg = (
                    "YouTube временно запросил подтверждение. "
                    "Включена защита мобильных клиентов, повторите попытку сейчас."
                )
            self.fail_task(task_id, f"Ошибка загрузки или обработки: {err_msg}")


task_manager = TaskManager()
