import os
import math
from typing import Dict, List, Tuple, Optional, Callable
import av
import ctranslate2

# PyAV 14+ removed 'metadata_errors' parameter from av.open,
# which causes older/current faster-whisper to raise TypeError in decode_audio().
_orig_av_open = av.open


def _safe_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)


av.open = _safe_av_open

from faster_whisper import WhisperModel

from app.models import TranscriptionSegment, WordItem, TranscriptionResult


def format_timestamp(seconds: float, srt_mode: bool = False) -> str:
    """Format seconds into SRT (HH:MM:SS,mmm) or VTT (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999

    delimiter = "," if srt_mode else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{delimiter}{millis:03d}"


def segments_to_srt(segments: List[TranscriptionSegment]) -> str:
    """Convert segments to SRT subtitle string."""
    lines = []
    for idx, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg.start, srt_mode=True)
        end_ts = format_timestamp(seg.end, srt_mode=True)
        lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{seg.text.strip()}\n")
    return "\n".join(lines)


def segments_to_vtt(segments: List[TranscriptionSegment]) -> str:
    """Convert segments to WebVTT subtitle string."""
    lines = ["WEBVTT\n"]
    for idx, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg.start, srt_mode=False)
        end_ts = format_timestamp(seg.end, srt_mode=False)
        lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{seg.text.strip()}\n")
    return "\n".join(lines)


def get_audio_duration(file_path: str) -> float:
    """Extract audio duration in seconds using PyAV."""
    try:
        with av.open(file_path) as container:
            if container.duration:
                return float(container.duration) / av.time_base
            for stream in container.streams.audio:
                if stream.duration and stream.time_base:
                    return float(stream.duration * stream.time_base)
    except Exception:
        pass
    return 0.0


class TranscriberManager:
    """Manages loaded Whisper models and execution."""

    def __init__(self):
        self._models: Dict[str, WhisperModel] = {}
        # Auto-detect CUDA if available, fallback to CPU
        has_cuda = False
        try:
            has_cuda = ctranslate2.get_cuda_device_count() > 0
        except Exception:
            pass

        default_device = "cuda" if has_cuda else "cpu"
        default_compute = "float16" if has_cuda else "int8"

        self.device = os.environ.get("WHISPER_DEVICE", default_device)
        self.compute_type = os.environ.get("WHISPER_COMPUTE_TYPE", default_compute)
        self.cpu_threads = int(os.environ.get("WHISPER_THREADS", "4"))

    def get_model(self, model_size: str = "base") -> WhisperModel:
        """Loads and caches the model in memory."""
        if model_size not in self._models:
            print(
                f"[Transcribator] Loading model '{model_size}' "
                f"(device={self.device}, compute={self.compute_type}, threads={self.cpu_threads})..."
            )
            model = WhisperModel(
                model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                num_workers=1,
            )
            self._models[model_size] = model
        return self._models[model_size]

    def transcribe(
        self,
        audio_path: str,
        task_id: str,
        filename: str,
        model_size: str = "small",
        language: Optional[str] = None,
        task: str = "transcribe",
        initial_prompt: Optional[str] = None,
        condition_on_previous_text: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> TranscriptionResult:
        """
        Transcribes the given audio file and reports progress.
        """
        model = self.get_model(model_size)
        total_duration = get_audio_duration(audio_path)

        # Run transcription with segment generator
        lang_arg = language if language and language != "auto" else None
        prompt_arg = initial_prompt.strip() if initial_prompt and initial_prompt.strip() else None

        segments_gen, info = model.transcribe(
            audio_path,
            language=lang_arg,
            task=task,
            beam_size=5,
            best_of=5,
            temperature=[0.0, 0.2, 0.4],
            word_timestamps=True,
            vad_filter=True,  # filters out non-speech segments
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400),
            condition_on_previous_text=condition_on_previous_text,
            repetition_penalty=1.12,
            no_repeat_ngram_size=3,
            hallucination_silence_threshold=2.0,
            initial_prompt=prompt_arg,
        )

        detected_language = info.language
        lang_prob = round(info.language_probability, 3)
        actual_duration = round(total_duration or getattr(info, "duration", 0.0) or 0.0, 2)

        transcription_segments: List[TranscriptionSegment] = []
        full_text_parts: List[str] = []

        seg_id = 0
        for seg in segments_gen:
            seg_id += 1
            words_list = []
            if seg.words:
                for w in seg.words:
                    words_list.append(
                        WordItem(
                            word=w.word,
                            start=round(w.start, 2),
                            end=round(w.end, 2),
                            probability=round(w.probability, 3),
                        )
                    )

            cleaned_text = seg.text.strip()
            if cleaned_text:
                full_text_parts.append(cleaned_text)

            t_seg = TranscriptionSegment(
                id=seg_id,
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=cleaned_text,
                words=words_list if words_list else None,
            )
            transcription_segments.append(t_seg)

            if seg.end > actual_duration:
                actual_duration = round(seg.end, 2)

            # Update progress
            if progress_callback and actual_duration > 0:
                pct = min(99, int((seg.end / actual_duration) * 100))
                progress_callback(pct)

        full_text = " ".join(full_text_parts)

        if progress_callback:
            progress_callback(100)

        return TranscriptionResult(
            task_id=task_id,
            filename=filename,
            text=full_text,
            language=detected_language,
            language_probability=lang_prob,
            duration=actual_duration,
            segments=transcription_segments,
        )


transcriber_manager = TranscriberManager()
