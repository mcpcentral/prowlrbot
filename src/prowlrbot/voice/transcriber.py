# -*- coding: utf-8 -*-
"""Speech-to-text transcription with pluggable backends."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

OPENAI_TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"


class TranscriberConfig(BaseModel):
    """Configuration for the speech-to-text transcriber."""

    backend: Literal["whisper_api", "whisper_local", "browser"] = "whisper_api"
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for whisper_api backend.",
    )
    model: str = Field(
        default="whisper-1",
        description="Whisper model name.",
    )
    language: Optional[str] = Field(
        default=None,
        description="ISO-639-1 language code (e.g. 'en'). None for auto-detect.",
    )


class WhisperTranscriber:
    """Transcribe audio files to text.

    Supports three backends:
    - ``whisper_api``: Calls the OpenAI Whisper transcription endpoint.
    - ``whisper_local``: Invokes the ``whisper`` CLI as a subprocess.
    - ``browser``: Placeholder; actual recognition runs client-side via
      the Web Speech API.
    """

    def __init__(self, config: TranscriberConfig) -> None:
        self.config = config

    async def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file and return the resulting text.

        Args:
            audio_path: Path to the audio file (wav, mp3, m4a, webm, etc.).

        Returns:
            Transcribed text string.

        Raises:
            FileNotFoundError: If *audio_path* does not exist.
            ValueError: If the configured backend is not supported.
            RuntimeError: If transcription fails.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self.config.backend == "whisper_api":
            return await self._transcribe_api(audio_path)
        elif self.config.backend == "whisper_local":
            return await self._transcribe_local(audio_path)
        elif self.config.backend == "browser":
            return self._transcribe_browser()
        else:
            raise ValueError(
                f"Unsupported transcriber backend: {self.config.backend}",
            )

    # ------------------------------------------------------------------
    # Backend implementations
    # ------------------------------------------------------------------

    async def _transcribe_api(self, audio_path: Path) -> str:
        """Call OpenAI Whisper API for transcription."""
        if not self.config.api_key:
            raise RuntimeError(
                "api_key is required for the whisper_api backend. "
                "Set it in TranscriberConfig or via the OPENAI_API_KEY env var.",
            )

        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        data = {"model": self.config.model}
        if self.config.language:
            data["language"] = self.config.language

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(audio_path, "rb") as f:
                files = {
                    "file": (audio_path.name, f, "application/octet-stream"),
                }
                response = await client.post(
                    OPENAI_TRANSCRIPTION_URL,
                    headers=headers,
                    data=data,
                    files=files,
                )

        if response.status_code != 200:
            raise RuntimeError(
                f"Whisper API returned {response.status_code}: {response.text}",
            )

        result = response.json()
        text = result.get("text", "")
        logger.info("Whisper API transcription complete (%d chars)", len(text))
        return text

    async def _transcribe_local(self, audio_path: Path) -> str:
        """Run the local ``whisper`` CLI as a subprocess.

        Uses asyncio.create_subprocess_exec which avoids shell injection
        by passing arguments as a list rather than through a shell.
        """
        cmd = [
            "whisper",
            str(audio_path),
            "--model",
            self.config.model,
            "--output_format",
            "txt",
            "--output_dir",
            str(audio_path.parent),
        ]
        if self.config.language:
            cmd.extend(["--language", self.config.language])

        logger.info("Running local whisper: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"whisper CLI exited with code {proc.returncode}: "
                f"{stderr.decode().strip()}",
            )

        # whisper CLI writes a .txt file next to the audio file
        txt_path = audio_path.with_suffix(".txt")
        if txt_path.exists():
            text = txt_path.read_text().strip()
            logger.info(
                "Local whisper transcription complete (%d chars)",
                len(text),
            )
            return text

        # Fallback: parse stdout
        text = stdout.decode().strip()
        logger.info(
            "Local whisper transcription from stdout (%d chars)",
            len(text),
        )
        return text

    @staticmethod
    def _transcribe_browser() -> str:
        """Placeholder for browser-based Speech Recognition.

        Actual recognition is performed client-side using the Web Speech API.
        The server returns an empty string so the frontend knows to activate
        the browser microphone.
        """
        return ""
