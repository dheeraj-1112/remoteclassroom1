from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Lecture
from .services.summarizer import summarize_transcript

logger = logging.getLogger(__name__)
_WHISPER_MODELS = {}


def _copy_source_to_temp(storage_key: str, suffix: str = ".mp4") -> str:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        with default_storage.open(storage_key, "rb") as source:
            shutil.copyfileobj(source, handle)
        handle.close()
        return handle.name
    except Exception:
        handle.close()
        Path(handle.name).unlink(missing_ok=True)
        raise


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _video_height(path: str) -> int:
    result = _run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=height", "-of", "csv=s=x:p=0", path,
    ])
    return int(result.stdout.strip().splitlines()[0])


def _store_hls_files(local_root: Path, lecture_id: int) -> str:
    """Copy a generated HLS tree into the configured Django storage backend."""
    version = str(time.time_ns())
    master_key = ""
    for file_path in sorted(local_root.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(local_root).as_posix()
        key = f"hls/lectures/{lecture_id}/{version}/{relative}"
        with file_path.open("rb") as source:
            saved = default_storage.save(key, ContentFile(source.read()))
        if relative == "master.m3u8":
            master_key = saved
    return master_key


@shared_task(bind=True, name="classroom.generate_hls")
def generate_hls(self, lecture_id: int):
    lecture = Lecture.objects.select_related("subject").filter(pk=lecture_id).first()
    if not lecture:
        return {"status": "missing", "lecture_id": lecture_id}

    lecture.hls_status = Lecture.ProcessingStatus.PROCESSING
    lecture.save(update_fields=["hls_status", "updated_at"])
    source_path = None
    temp_root = None
    try:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise RuntimeError("FFmpeg and ffprobe are required for adaptive-bitrate processing. Install FFmpeg and restart the worker.")
        suffix = Path(lecture.video.name).suffix or ".mp4"
        source_path = _copy_source_to_temp(lecture.video.name, suffix)
        height = _video_height(source_path)
        # Only create renditions at or below the source resolution (minimum one 240p rendition).
        renditions = [value for value in (240, 360, 480, 720) if value <= height]
        if not renditions:
            renditions = [max(144, height - (height % 2))]

        temp_root = Path(tempfile.mkdtemp(prefix=f"lecture-{lecture_id}-hls-"))
        master_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
        bandwidths = {240: 450000, 360: 800000, 480: 1400000, 720: 2800000}
        for rendition in renditions:
            variant_dir = temp_root / f"{rendition}p"
            variant_dir.mkdir(parents=True, exist_ok=True)
            playlist = variant_dir / "index.m3u8"
            segment_template = variant_dir / "segment_%03d.ts"
            _run([
                "ffmpeg", "-y", "-i", source_path,
                "-vf", f"scale=-2:{rendition}:force_original_aspect_ratio=decrease",
                "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "main", "-crf", "24",
                "-c:a", "aac", "-b:a", "96k", "-ac", "2",
                "-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod",
                "-hls_segment_filename", str(segment_template), str(playlist),
            ])
            bandwidth = bandwidths.get(rendition, 350000)
            master_lines.extend([
                f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth}",
                f"{rendition}p/index.m3u8",
            ])

        (temp_root / "master.m3u8").write_text("\n".join(master_lines) + "\n", encoding="utf-8")
        master_key = _store_hls_files(temp_root, lecture.id)
        lecture.hls_master_key = master_key
        lecture.hls_status = Lecture.ProcessingStatus.READY
        lecture.save(update_fields=["hls_master_key", "hls_status", "updated_at"])
        return {"status": "ready", "lecture_id": lecture.id, "renditions": renditions}
    except Exception as exc:
        logger.exception("HLS generation failed for lecture %s", lecture_id)
        lecture.hls_status = Lecture.ProcessingStatus.FAILED
        lecture.save(update_fields=["hls_status", "updated_at"])
        return {"status": "failed", "lecture_id": lecture.id, "error": str(exc)}
    finally:
        if source_path:
            Path(source_path).unlink(missing_ok=True)
        if temp_root:
            shutil.rmtree(temp_root, ignore_errors=True)


@shared_task(bind=True, name="classroom.generate_lecture_summary")
def generate_lecture_summary(self, lecture_id: int):
    lecture = Lecture.objects.filter(pk=lecture_id).first()
    if not lecture:
        return {"status": "missing", "lecture_id": lecture_id}

    lecture.summary_status = Lecture.ProcessingStatus.PROCESSING
    lecture.summary_error = ""
    lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
    source_path = None
    try:
        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError("OpenAI Whisper is not installed in the processing worker. Install backend/requirements.txt and restart the worker.") from exc

        suffix = Path(lecture.video.name).suffix or ".mp4"
        source_path = _copy_source_to_temp(lecture.video.name, suffix)
        model_name = getattr(settings, "WHISPER_MODEL", "base")
        if model_name not in _WHISPER_MODELS:
            _WHISPER_MODELS[model_name] = whisper.load_model(model_name)
        model = _WHISPER_MODELS[model_name]
        language = getattr(settings, "WHISPER_LANGUAGE", "") or None
        result = model.transcribe(source_path, fp16=False, language=language, verbose=False)
        transcript = (result.get("text") or "").strip()
        if not transcript:
            raise RuntimeError("Whisper did not detect speech in this recording. Check that the uploaded video contains clear audio.")

        summary, count = summarize_transcript(transcript, minimum_words=300, maximum_words=500)
        lecture.transcript = transcript
        lecture.summary = summary
        lecture.summary_word_count = count
        lecture.transcription_language = result.get("language", "")
        lecture.summary_status = Lecture.ProcessingStatus.READY
        lecture.summary_error = ""
        lecture.summary_generated_at = timezone.now()
        lecture.save(update_fields=[
            "transcript", "summary", "summary_word_count", "transcription_language",
            "summary_status", "summary_error", "summary_generated_at", "updated_at",
        ])
        return {"status": "ready", "lecture_id": lecture.id, "summary_words": count, "language": lecture.transcription_language}
    except Exception as exc:
        logger.exception("Lecture summarization failed for lecture %s", lecture_id)
        lecture.summary_status = Lecture.ProcessingStatus.FAILED
        lecture.summary_error = str(exc)[:2000]
        lecture.save(update_fields=["summary_status", "summary_error", "updated_at"])
        return {"status": "failed", "lecture_id": lecture.id, "error": str(exc)}
    finally:
        if source_path:
            Path(source_path).unlink(missing_ok=True)
