"""Transcribe a small lecture video with the Groq-hosted Whisper API.

Used only by FREE_TIER_MODE deployments. The full/local deployment continues
to use the open-source OpenAI Whisper package through Celery tasks.
"""
from __future__ import annotations

import os
import requests

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class TranscriptionError(RuntimeError):
    pass


def transcribe_video(file_obj, filename: str, api_key: str, model: str, language: str = ""):
    if not api_key:
        raise TranscriptionError(
            "Speech-to-text is not configured. Add a Groq API key to the GROQ_API_KEY environment variable."
        )
    try:
        response = requests.post(
            GROQ_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            data={
                "model": model,
                "response_format": "verbose_json",
                "temperature": "0",
                **({"language": language} if language else {}),
            },
            files={"file": (os.path.basename(filename), file_obj, "application/octet-stream")},
            timeout=(15, 90),
        )
    except requests.Timeout as exc:
        raise TranscriptionError("The transcription service took too long. Try a shorter video.") from exc
    except requests.RequestException as exc:
        raise TranscriptionError("Could not connect to the transcription service. Please try again.") from exc

    if response.status_code == 429:
        raise TranscriptionError("The free transcription quota is temporarily exhausted. Try again later.")
    if response.status_code in (401, 403):
        raise TranscriptionError("The transcription API key was rejected. Check GROQ_API_KEY in Render settings.")
    if response.status_code == 413:
        raise TranscriptionError("The video is larger than the transcription service's 25 MB free-tier limit.")
    if not response.ok:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            detail = response.text[:300]
        raise TranscriptionError(f"Transcription service error ({response.status_code}): {detail or 'Unknown error'}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise TranscriptionError("The transcription service returned an invalid response.") from exc
    transcript = (payload.get("text") or "").strip()
    if not transcript:
        raise TranscriptionError("No speech was detected in this recording. Try a video with clearer audio.")
    return transcript, payload.get("language", "")
