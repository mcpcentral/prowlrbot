# -*- coding: utf-8 -*-
"""Text-to-speech synthesis with pluggable backends."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"


class SynthesizerConfig(BaseModel):
    """Configuration for the text-to-speech synthesizer."""

    backend: Literal["browser", "openai_tts"] = "browser"
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for the openai_tts backend.",
    )
    voice: str = Field(
        default="alloy",
        description="Voice name for TTS. Options: alloy, echo, fable, onyx, nova, shimmer.",
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Playback speed multiplier (0.25 - 4.0).",
    )
    model: str = Field(
        default="tts-1",
        description="TTS model name (tts-1 or tts-1-hd).",
    )


class TextToSpeech:
    """Synthesize speech from text.

    Supports two backends:
    - ``openai_tts``: Calls the OpenAI TTS endpoint and writes an MP3 file.
    - ``browser``: Placeholder; actual synthesis runs client-side via the
      Web Speech Synthesis API.
    """

    def __init__(self, config: SynthesizerConfig) -> None:
        self.config = config

    async def synthesize(self, text: str, output_path: Path) -> Optional[Path]:
        """Generate an audio file from text.

        Args:
            text: The text to convert to speech.
            output_path: Where to write the resulting audio file.

        Returns:
            The *output_path* on success, or ``None`` when the browser
            backend is selected (synthesis happens client-side).

        Raises:
            ValueError: If the configured backend is not supported.
            RuntimeError: If synthesis fails.
        """
        if self.config.backend == "openai_tts":
            return await self._synthesize_openai(text, Path(output_path))
        elif self.config.backend == "browser":
            return self._synthesize_browser()
        else:
            raise ValueError(
                f"Unsupported synthesizer backend: {self.config.backend}",
            )

    # ------------------------------------------------------------------
    # Backend implementations
    # ------------------------------------------------------------------

    async def _synthesize_openai(self, text: str, output_path: Path) -> Path:
        """Call the OpenAI TTS API and write the audio to *output_path*."""
        if not self.config.api_key:
            raise RuntimeError(
                "api_key is required for the openai_tts backend. "
                "Set it in SynthesizerConfig or via the OPENAI_API_KEY env var.",
            )

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "input": text,
            "voice": self.config.voice,
            "speed": self.config.speed,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENAI_TTS_URL,
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenAI TTS API returned {response.status_code}: {response.text}",
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        logger.info(
            "TTS synthesis complete: %s (%d bytes)",
            output_path,
            len(response.content),
        )
        return output_path

    @staticmethod
    def _synthesize_browser() -> None:
        """Placeholder for browser-based Speech Synthesis.

        Actual synthesis is performed client-side using the Web Speech
        Synthesis API. The server returns ``None`` so the frontend knows
        to use the browser voice.
        """
        return None
