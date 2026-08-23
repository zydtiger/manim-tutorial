from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..config.models import TTSConfig
from .base import TutorialSpeechService


def build_voiceover_input_data(text: str, config: TTSConfig) -> dict[str, Any]:
    """Build the cache identity required by manim-voiceover 0.4."""
    return {
        "input_text": text,
        "service": "qwen3",
        "config": {
            "model": config.model,
            "voice": config.voice,
            "language": config.language,
            "device": config.device,
            "rate": config.rate,
        },
    }


def build_voiceover_input_data_clone(
    text: str, config: TTSConfig, ref_audio_sha256: str
) -> dict[str, Any]:
    """Build the cache identity for the qwen3-clone provider.

    The reference recording is identified by content hash, never by its local
    filesystem path, so the cache identity stays portable and safe to share.
    """
    return {
        "input_text": text,
        "service": "qwen3-clone",
        "config": {
            "model": config.model,
            "ref_audio_sha256": ref_audio_sha256,
            "ref_text": config.ref_text,
            "language": config.language,
            "device": config.device,
            "rate": config.rate,
        },
    }


def reference_audio_sha256(path: Path) -> str:
    """Content fingerprint for a voice-clone reference recording."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_atempo_command(source: Path, target: Path, rate: float) -> list[str]:
    """Build the pitch-preserving FFmpeg command used for narration rate."""
    return [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-filter:a",
        f"atempo={rate:g}",
        str(target),
    ]


def resolve_device(requested: str, torch_module: Any) -> str:
    if requested == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch_module.cuda.is_available():
        raise RuntimeError("tts.device is cuda but CUDA is unavailable")
    return requested


def write_narration_audio(
    audio: Any,
    sample_rate: int,
    *,
    target: Path,
    rate: float,
    audio_directory: Path,
    soundfile_module: Any,
) -> None:
    """Write one synthesized beat to `target`, applying the configured rate.

    Shared by every provider's inner Manim Voiceover SpeechService so the
    numbered-beat output convention and FFmpeg atempo handling exist once.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if rate == 1.0:
        soundfile_module.write(target, audio, sample_rate)
        return
    with tempfile.TemporaryDirectory(
        prefix=".narration-", dir=audio_directory
    ) as temporary_directory:
        source = Path(temporary_directory) / "source.wav"
        soundfile_module.write(source, audio, sample_rate)
        target.unlink(missing_ok=True)
        try:
            subprocess.run(
                build_atempo_command(source, target, rate),
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "FFmpeg is required to apply the configured narration rate."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "FFmpeg failed while applying the configured narration rate."
            ) from exc


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
                wavs, sample_rate = model.generate_custom_voice(
                    text=text, language=config.language, speaker=config.voice
                )
                audio = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
                write_narration_audio(
                    audio,
                    sample_rate,
                    target=target,
                    rate=config.rate,
                    audio_directory=audio_directory,
                    soundfile_module=sf,
                )
                return VoiceoverData(
                    input_text=text,
                    input_data=build_voiceover_input_data(text, config),
                    original_audio=str(target),
                )

        return _VoiceoverQwenService()


class Qwen3CloneSpeechService(TutorialSpeechService):
    """Lazy local Qwen3 Base voice-clone adapter for Manim Voiceover."""

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
        assert config.ref_audio is not None and config.ref_text is not None  # loader invariant
        device = resolve_device(config.device, torch)
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        model = Qwen3TTSModel.from_pretrained(
            config.model,
            device_map="cuda:0" if device == "cuda" else "cpu",
            dtype=dtype,
        )
        # Build the clone prompt once per render (ICL mode: ref_text supplied,
        # x_vector_only_mode left at its default False) and reuse it for every
        # beat instead of rebuilding it from the reference recording each time.
        voice_clone_prompt = model.create_voice_clone_prompt(
            ref_audio=str(config.ref_audio), ref_text=config.ref_text
        )
        ref_audio_hash = reference_audio_sha256(config.ref_audio)

        class _VoiceoverQwenCloneService(SpeechService):
            def __init__(self):
                super().__init__()
                self._beat_number = 0

            def generate_from_text(self, text: str, cache_dir=None, path=None, **kwargs):
                self._beat_number += 1
                target = audio_directory / f"beat_{self._beat_number:03}.wav"
                wavs, sample_rate = model.generate_voice_clone(
                    text=text, language=config.language, voice_clone_prompt=voice_clone_prompt
                )
                audio = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
                write_narration_audio(
                    audio,
                    sample_rate,
                    target=target,
                    rate=config.rate,
                    audio_directory=audio_directory,
                    soundfile_module=sf,
                )
                return VoiceoverData(
                    input_text=text,
                    input_data=build_voiceover_input_data_clone(text, config, ref_audio_hash),
                    original_audio=str(target),
                )

        return _VoiceoverQwenCloneService()
