import os
import shutil
import threading
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.models import TaskStatus, ModelInfo
from app.tasks import task_manager
from app.transcriber import segments_to_srt, segments_to_vtt, transcriber_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "..", "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Transcribator API",
    description="Local Speech-to-Text Micro-SaaS API powered by faster-whisper",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AVAILABLE_MODELS: List[ModelInfo] = [
    ModelInfo(
        id="small",
        name="Small (~244M) [Рекомендуется для CPU]",
        description="Отличная точность для русской речи и диалогов на обычном процессоре",
        vram_ram="~2 GB RAM",
        relative_speed="~6x",
    ),
    ModelInfo(
        id="large-v3-turbo",
        name="Turbo (~800M) [Флагманское качество]",
        description="Качество Large-v3 при высокой скорости, отлично распознает сленг и акценты",
        vram_ram="~3 GB RAM",
        relative_speed="~8x",
    ),
    ModelInfo(
        id="base",
        name="Base (~74M)",
        description="Быстрая базовая модель для простых и четких записей",
        vram_ram="~1 GB RAM",
        relative_speed="~16x",
    ),
    ModelInfo(
        id="tiny",
        name="Tiny (~39M)",
        description="Сверхбыстрая модель, подходит для быстрого черновика",
        vram_ram="~1 GB RAM",
        relative_speed="~32x",
    ),
    ModelInfo(
        id="medium",
        name="Medium (~769M)",
        description="Высокая точность для сложных аудиозаписей",
        vram_ram="~4 GB RAM",
        relative_speed="~2x",
    ),
    ModelInfo(
        id="large-v3",
        name="Large v3 (~1550M)",
        description="Максимальное качество распознавания и пунктуации",
        vram_ram="~6 GB RAM",
        relative_speed="~1x",
    ),
]


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Transcribator",
        "version": "1.0.0",
        "device": transcriber_manager.device,
        "compute_type": transcriber_manager.compute_type,
    }


@app.get("/api/models", response_model=List[ModelInfo])
def get_models():
    """Get list of supported models."""
    return AVAILABLE_MODELS


@app.post("/api/transcribe")
async def start_transcription(
    file: UploadFile = File(...),
    model_size: str = Form("small"),
    language: Optional[str] = Form("auto"),
    task: str = Form("transcribe"),
    initial_prompt: Optional[str] = Form(None),
    condition_on_previous_text: bool = Form(False),
):
    """
    Upload an audio/video file and start asynchronous transcription.
    Returns task_id for tracking progress.
    """
    allowed_exts = {
        ".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac", ".aac",
        ".mp4", ".mov", ".mkv", ".wma", ".opus"
    }
    raw_filename = file.filename or "audio.mp3"
    safe_filename = os.path.basename(raw_filename)
    ext = os.path.splitext(safe_filename)[1].lower()

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат '{ext}'. Допустимые форматы: {', '.join(sorted(allowed_exts))}"
        )

    task_id = task_manager.create_task(filename=safe_filename, model_name=model_size)
    save_path = os.path.join(UPLOADS_DIR, f"{task_id}_{safe_filename}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    thread = threading.Thread(
        target=task_manager.run_transcription,
        args=(task_id, save_path, safe_filename, model_size, language, task, initial_prompt, condition_on_previous_text),
        daemon=True,
    )
    thread.start()

    return {"task_id": task_id, "status": "queued", "filename": safe_filename}


@app.post("/api/transcribe-url")
async def start_url_transcription(
    url: str = Form(...),
    model_size: str = Form("small"),
    language: Optional[str] = Form("ru"),
    task: str = Form("transcribe"),
    initial_prompt: Optional[str] = Form(None),
    condition_on_previous_text: bool = Form(False),
):
    """
    Download audio from video URL (YouTube, Facebook, Rutube, VK, TikTok, etc.)
    and start asynchronous transcription.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Некорректная ссылка. Ссылка должна начинаться с http:// или https://"
        )

    task_id = task_manager.create_task(filename=clean_url, model_name=model_size)

    thread = threading.Thread(
        target=task_manager.run_url_transcription,
        args=(
            task_id,
            clean_url,
            UPLOADS_DIR,
            model_size,
            language,
            task,
            initial_prompt,
            condition_on_previous_text,
        ),
        daemon=True,
    )
    thread.start()

    return {"task_id": task_id, "status": "queued", "filename": clean_url}


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """Get status and result of a transcription task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@app.get("/api/export/{task_id}/{export_format}")
def export_transcription(task_id: str, export_format: str):
    """
    Download transcription in specified format: txt, docx (also srt, vtt, json).
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task.status != "completed" or not task.result:
        raise HTTPException(status_code=400, detail="Задача еще не завершена")

    base_name = os.path.splitext(task.filename)[0]
    result = task.result

    from urllib.parse import quote

    if export_format == "txt":
        content = result.text
        encoded_filename = quote(f"{base_name}.txt")
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=\"transcription.txt\"; filename*=UTF-8''{encoded_filename}"
            },
        )
    elif export_format == "docx":
        import io
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # Document Header
        title_p = doc.add_heading(base_name, level=1)
        title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Meta info
        mins = int(result.duration // 60)
        secs = int(result.duration % 60)
        dur_str = f"{mins} мин {secs:02d} сек" if mins > 0 else f"{secs} сек"

        meta_p = doc.add_paragraph()
        meta_run = meta_p.add_run(
            f"Язык: {result.language.upper()} ({int(result.language_probability * 100)}%)  |  Длительность: {dur_str}"
        )
        meta_run.font.size = Pt(9.5)
        meta_run.font.italic = True
        meta_run.font.color.rgb = RGBColor(128, 128, 128)

        doc.add_paragraph()

        # Text paragraphs
        full_text = result.text.strip()
        for p_text in full_text.split("\n"):
            clean = p_text.strip()
            if clean:
                p = doc.add_paragraph(clean)
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(8)

        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)

        encoded_filename = quote(f"{base_name}.docx")
        return Response(
            content=stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename=\"transcription.docx\"; filename*=UTF-8''{encoded_filename}"
            },
        )
    elif export_format == "srt":
        content = segments_to_srt(result.segments)
        encoded_filename = quote(f"{base_name}.srt")
        return Response(
            content=content,
            media_type="application/x-subrip; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"transcription.srt\"; filename*=UTF-8''{encoded_filename}"},
        )
    elif export_format == "vtt":
        content = segments_to_vtt(result.segments)
        encoded_filename = quote(f"{base_name}.vtt")
        return Response(
            content=content,
            media_type="text/vtt; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"transcription.vtt\"; filename*=UTF-8''{encoded_filename}"},
        )
    elif export_format == "json":
        return JSONResponse(
            content=result.model_dump(),
            headers={"Content-Disposition": f'attachment; filename="{base_name}.json"'},
        )
    else:
        raise HTTPException(status_code=400, detail="Неверный формат (доступны: txt, docx)")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Transcribator is running</h1><p>UI is initializing...</p>")
