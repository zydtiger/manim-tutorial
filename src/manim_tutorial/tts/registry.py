from __future__ import annotations

from pathlib import Path

from ..config.models import TTSConfig
from .qwen import Qwen3CloneSpeechService, Qwen3SpeechService, reference_audio_sha256


def create_speech_service(config: TTSConfig, *, audio_directory: Path):
    if config.provider == "qwen3":
        return Qwen3SpeechService(config).build_voiceover_service(audio_directory=audio_directory)
    if config.provider == "qwen3-clone":
        return Qwen3CloneSpeechService(config).build_voiceover_service(
            audio_directory=audio_directory
        )
    # Unreachable once config validation has run; kept as a defensive guard.
    raise ValueError(f"Unsupported TTS provider: {config.provider}")


def timeline_identity(config: TTSConfig) -> dict[str, str]:
    """Identify narration in the timeline manifest without a local path."""
    if config.provider == "qwen3-clone":
        assert config.ref_audio is not None  # loader invariant
        return {"provider": "qwen3-clone", "reference": reference_audio_sha256(config.ref_audio)}
    assert config.voice is not None  # loader invariant
    return {"provider": config.provider, "voice": config.voice}
