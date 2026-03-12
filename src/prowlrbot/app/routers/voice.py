# -*- coding: utf-8 -*-
"""Voice interaction API routes for ProwlrBot dashboard."""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from prowlrbot.voice.transcriber import TranscriberConfig, WhisperTranscriber
from prowlrbot.voice.synthesizer import SynthesizerConfig, TextToSpeech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Temporary directory for voice files
VOICE_TMP_DIR = Path(tempfile.gettempdir()) / "prowlrbot_voice"
VOICE_TMP_DIR.mkdir(parents=True, exist_ok=True)

# Allowed audio MIME types for upload
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
    "application/octet-stream",  # fallback for browsers that don't set type
}


class TranscribeResponse(BaseModel):
    """Response from the transcribe endpoint."""

    text: str
    backend: str


class SynthesizeRequest(BaseModel):
    """Request body for the synthesize endpoint."""

    text: str = Field(..., min_length=1, max_length=4096)
    voice: str = "alloy"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    backend: str = "openai_tts"


class SynthesizeResponse(BaseModel):
    """Response from the synthesize endpoint when using browser backend."""

    backend: str
    message: str


def _get_api_key() -> str | None:
    """Resolve the OpenAI API key from environment."""
    return os.environ.get("OPENAI_API_KEY")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    backend: str = Form(default="whisper_api"),
    language: str | None = Form(default=None),
    model: str = Form(default="whisper-1"),
):
    """Upload an audio file and receive transcribed text.

    Supported backends:
    - ``whisper_api`` — OpenAI Whisper API (requires OPENAI_API_KEY).
    - ``whisper_local`` — Local whisper CLI installation.
    - ``browser`` — Returns empty text; transcription handled client-side.
    """
    if backend == "browser":
        return TranscribeResponse(text="", backend="browser")

    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_TYPES))}",
        )

    # Save uploaded file to temp directory
    suffix = Path(file.filename).suffix if file.filename else ".webm"
    audio_path = VOICE_TMP_DIR / f"{uuid.uuid4().hex}{suffix}"

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        if len(contents) > 25 * 1024 * 1024:  # 25 MB limit (OpenAI's limit)
            raise HTTPException(
                status_code=400,
                detail="Audio file too large. Maximum size is 25 MB.",
            )

        audio_path.write_bytes(contents)

        config = TranscriberConfig(
            backend=backend,
            api_key=_get_api_key(),
            model=model,
            language=language,
        )
        transcriber = WhisperTranscriber(config)
        text = await transcriber.transcribe(audio_path)

        return TranscribeResponse(text=text, backend=backend)

    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        logger.error("Transcription failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during transcription")
        raise HTTPException(status_code=500, detail="Internal transcription error")
    finally:
        # Clean up temp file
        if audio_path.exists():
            audio_path.unlink(missing_ok=True)


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """Convert text to speech and return an audio file.

    Supported backends:
    - ``openai_tts`` — OpenAI TTS API (requires OPENAI_API_KEY).
      Returns an MP3 audio file.
    - ``browser`` — Returns JSON indicating client-side synthesis.
    """
    if request.backend == "browser":
        return SynthesizeResponse(
            backend="browser",
            message="Use browser Speech Synthesis API for playback.",
        )

    if request.backend != "openai_tts":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported synthesizer backend: {request.backend}",
        )

    output_path = VOICE_TMP_DIR / f"{uuid.uuid4().hex}.mp3"

    try:
        config = SynthesizerConfig(
            backend="openai_tts",
            api_key=_get_api_key(),
            voice=request.voice,
            speed=request.speed,
        )
        tts = TextToSpeech(config)
        result_path = await tts.synthesize(request.text, output_path)

        if result_path is None or not result_path.exists():
            raise HTTPException(
                status_code=500, detail="TTS synthesis produced no output."
            )

        return FileResponse(
            path=str(result_path),
            media_type="audio/mpeg",
            filename="speech.mp3",
            background=None,  # Don't delete before sending
        )

    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error("Synthesis failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during synthesis")
        raise HTTPException(status_code=500, detail="Internal synthesis error")
