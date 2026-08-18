from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config.models import TTSConfig
from .base import TutorialSpeechService


def build_voiceover_input_data(text: str, config: TTSConfig) -> dict[str, object]:
    """Build the cache identity required by manim-voiceover 0.4."""
    return {
        "input_text": text,
        "service": "qwen3",
        "config": {
            "model": config.model,
            "voice": config.voice,
            "language": config.language,
            "device": config.device,
        },
    }


def resolve_device(requested: str, torch_module: Any) -> str:
    if requested == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch_module.cuda.is_available():
        raise RuntimeError("tts.device is cuda but CUDA is unavailable")
    return requested


class Qwen3SpeechService(TutorialSpeechService):
    """Lazy local Qwen3 CustomVoice adapter for Manim Voiceover."""

    def __init__(self, config: TTSConfig):
        self.config = config

    def build_voiceover_service(self, *, audio_directory: Path):
        try:
            import numpy as np
            import soundfile as sf
            import torch
            from manim_voiceover.services.base import SpeechService, VoiceoverData
            from qwen_tts import Qwen3TTSModel
        except ImportError as exc:  # pragma: no cover - depends on runtime install
            raise RuntimeError(
                "Qwen3 TTS runtime dependencies are unavailable. Run uv sync before rendering."
            ) from exc

        config = self.config
        device = resolve_device(config.device, torch)
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        model = Qwen3TTSModel.from_pretrained(
            config.model,
            device_map="cuda:0" if device == "cuda" else "cpu",
            dtype=dtype,
        )

        class _VoiceoverQwenService(SpeechService):
            def __init__(self):
                super().__init__()
                self._beat_number = 0

            def generate_from_text(self, text: str, cache_dir=None, path=None, **kwargs):
                # Final artifacts are numbered narration beats, not an opaque
                # Voiceover cache. Regenerate to prevent stale audio when the
                # model, voice, language, or device changes between renders.
                self._beat_number += 1
                target = audio_directory / f"beat_{self._beat_number:03}.wav"
                target.parent.mkdir(parents=True, exist_ok=True)
                wavs, sample_rate = model.generate_custom_voice(
                    text=text, language=config.language, speaker=config.voice
                )
                audio = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
                sf.write(target, audio, sample_rate)
                return VoiceoverData(
                    input_text=text,
                    input_data=build_voiceover_input_data(text, config),
                    original_audio=str(target),
                )

        return _VoiceoverQwenService()
