from __future__ import annotations

from pathlib import Path

from ..config.models import TTSConfig
from .qwen import Qwen3SpeechService


def create_speech_service(config: TTSConfig, *, audio_directory: Path):
    if config.provider != "qwen3":  # protected by config validation
        raise ValueError(f"Unsupported TTS provider: {config.provider}")
    return Qwen3SpeechService(config).build_voiceover_service(audio_directory=audio_directory)
