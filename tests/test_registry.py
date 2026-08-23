from pathlib import Path

import pytest

from manim_tutorial.config.models import TTSConfig
from manim_tutorial.tts.qwen import reference_audio_sha256
from manim_tutorial.tts.registry import create_speech_service, timeline_identity

QWEN3_CONFIG = TTSConfig(
    provider="qwen3",
    model="Qwen/model",
    voice="Ryan",
    language="English",
    device="cpu",
    rate=1.15,
)


def test_create_speech_service_rejects_unknown_provider(tmp_path: Path):
    config = TTSConfig(
        provider="unsupported",
        model="model",
        voice="Ryan",
        language="English",
        device="cpu",
        rate=1.0,
    )
    with pytest.raises(ValueError, match="Unsupported TTS provider: unsupported"):
        create_speech_service(config, audio_directory=tmp_path)


def test_create_speech_service_dispatches_qwen3_clone(tmp_path: Path, monkeypatch):
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake reference audio bytes")
    clone_config = TTSConfig(
        provider="qwen3-clone",
        model="Qwen/model-Base",
        voice=None,
        language="English",
        device="cpu",
        rate=1.0,
        ref_audio=ref_audio,
        ref_text="Hello, this is my voice.",
    )
    calls = []

    class _FakeCloneService:
        def __init__(self, config):
            self.config = config

        def build_voiceover_service(self, *, audio_directory):
            calls.append((self.config, audio_directory))
            return "clone-service"

    monkeypatch.setattr("manim_tutorial.tts.registry.Qwen3CloneSpeechService", _FakeCloneService)
    result = create_speech_service(clone_config, audio_directory=tmp_path)
    assert result == "clone-service"
    assert calls == [(clone_config, tmp_path)]


def test_timeline_identity_for_qwen3_reports_provider_and_voice():
    assert timeline_identity(QWEN3_CONFIG) == {"provider": "qwen3", "voice": "Ryan"}


def test_timeline_identity_for_clone_reports_provider_and_reference_hash(tmp_path: Path):
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake reference audio bytes")
    clone_config = TTSConfig(
        provider="qwen3-clone",
        model="Qwen/model-Base",
        voice=None,
        language="English",
        device="cpu",
        rate=1.0,
        ref_audio=ref_audio,
        ref_text="Hello, this is my voice.",
    )
    identity = timeline_identity(clone_config)
    assert identity == {"provider": "qwen3-clone", "reference": reference_audio_sha256(ref_audio)}
    assert str(ref_audio) not in identity.values()
