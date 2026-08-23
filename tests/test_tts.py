import dataclasses
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from manim_tutorial.config.models import TTSConfig
from manim_tutorial.tts.qwen import (
    Qwen3CloneSpeechService,
    build_atempo_command,
    build_voiceover_input_data,
    build_voiceover_input_data_clone,
    reference_audio_sha256,
    resolve_device,
)


class _Cuda:
    def __init__(self, available: bool):
        self.available = available

    def is_available(self) -> bool:
        return self.available


class _Torch:
    def __init__(self, available: bool):
        self.cuda = _Cuda(available)


def test_resolve_auto_device():
    assert resolve_device("auto", _Torch(True)) == "cuda"
    assert resolve_device("auto", _Torch(False)) == "cpu"


def test_reject_unavailable_cuda():
    with pytest.raises(RuntimeError, match="unavailable"):
        resolve_device("cuda", _Torch(False))


def test_voiceover_input_data_matches_cache_contract():
    config = TTSConfig(
        provider="qwen3",
        model="Qwen/model",
        voice="Ryan",
        language="English",
        device="auto",
        rate=1.15,
    )
    assert build_voiceover_input_data("Explain eigenvectors.", config) == {
        "input_text": "Explain eigenvectors.",
        "service": "qwen3",
        "config": {
            "model": "Qwen/model",
            "voice": "Ryan",
            "language": "English",
            "device": "auto",
            "rate": 1.15,
        },
    }


def test_atempo_command_preserves_pitch_with_configured_rate(tmp_path):
    source = tmp_path / "source.wav"
    target = tmp_path / "target.wav"
    assert build_atempo_command(source, target, 1.15) == [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-filter:a",
        "atempo=1.15",
        str(target),
    ]


def test_reference_audio_sha256_matches_file_bytes(tmp_path):
    path = tmp_path / "reference.wav"
    path.write_bytes(b"fake reference audio bytes")
    assert reference_audio_sha256(path) == hashlib.sha256(b"fake reference audio bytes").hexdigest()


_BASE_CLONE_CONFIG = TTSConfig(
    provider="qwen3-clone",
    model="Qwen/model-Base",
    voice=None,
    language="English",
    device="cpu",
    rate=1.0,
    ref_audio=Path("/reference.wav"),
    ref_text="Hello, this is my voice.",
)


def _clone_config(**overrides) -> TTSConfig:
    return dataclasses.replace(_BASE_CLONE_CONFIG, **overrides)


def test_voiceover_input_data_clone_identifies_reference_by_hash_not_path():
    config = _clone_config()
    assert build_voiceover_input_data_clone("Explain eigenvectors.", config, "deadbeef") == {
        "input_text": "Explain eigenvectors.",
        "service": "qwen3-clone",
        "config": {
            "model": "Qwen/model-Base",
            "ref_audio_sha256": "deadbeef",
            "ref_text": "Hello, this is my voice.",
            "language": "English",
            "device": "cpu",
            "rate": 1.0,
        },
    }


class _FakeCloneModel:
    def __init__(self):
        self.create_voice_clone_prompt_calls: list[dict] = []
        self.generate_voice_clone_calls: list[dict] = []

    def create_voice_clone_prompt(self, *, ref_audio, ref_text):
        self.create_voice_clone_prompt_calls.append({"ref_audio": ref_audio, "ref_text": ref_text})
        return ["FAKE_VOICE_CLONE_PROMPT"]

    def generate_voice_clone(self, *, text, language, voice_clone_prompt):
        self.generate_voice_clone_calls.append(
            {"text": text, "language": language, "voice_clone_prompt": voice_clone_prompt}
        )
        return [np.zeros(8, dtype=np.float32)], 16000


class _FakeQwen3TTSModel:
    last_instance: _FakeCloneModel | None = None

    @classmethod
    def from_pretrained(cls, model, *, device_map, dtype):
        cls.last_instance = _FakeCloneModel()
        return cls.last_instance


def _install_fake_qwen_runtime(monkeypatch):
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: False),
        float32="float32-dtype",
        bfloat16="bfloat16-dtype",
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "qwen_tts", SimpleNamespace(Qwen3TTSModel=_FakeQwen3TTSModel))


def test_clone_service_builds_prompt_once_and_reuses_it_across_beats(tmp_path, monkeypatch):
    _install_fake_qwen_runtime(monkeypatch)
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake reference audio bytes")
    config = _clone_config(ref_audio=ref_audio, rate=1.0)

    service = Qwen3CloneSpeechService(config).build_voiceover_service(audio_directory=tmp_path)
    first = service.generate_from_text("Beat one.")
    second = service.generate_from_text("Beat two.")

    model = _FakeQwen3TTSModel.last_instance
    assert len(model.create_voice_clone_prompt_calls) == 1
    assert model.create_voice_clone_prompt_calls[0] == {
        "ref_audio": str(ref_audio),
        "ref_text": "Hello, this is my voice.",
    }
    assert len(model.generate_voice_clone_calls) == 2
    prompt = model.generate_voice_clone_calls[0]["voice_clone_prompt"]
    assert prompt == ["FAKE_VOICE_CLONE_PROMPT"]
    assert model.generate_voice_clone_calls[1]["voice_clone_prompt"] is prompt

    expected_hash = reference_audio_sha256(ref_audio)
    assert first["input_data"] == {
        "input_text": "Beat one.",
        "service": "qwen3-clone",
        "config": {
            "model": "Qwen/model-Base",
            "ref_audio_sha256": expected_hash,
            "ref_text": "Hello, this is my voice.",
            "language": "English",
            "device": "cpu",
            "rate": 1.0,
        },
    }
    assert Path(first["original_audio"]) == tmp_path / "beat_001.wav"
    assert Path(second["original_audio"]) == tmp_path / "beat_002.wav"
    assert Path(first["original_audio"]).is_file()
    assert Path(second["original_audio"]).is_file()


def test_clone_service_applies_atempo_when_rate_is_not_one(tmp_path, monkeypatch):
    _install_fake_qwen_runtime(monkeypatch)
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake reference audio bytes")
    config = _clone_config(ref_audio=ref_audio, rate=1.15)

    service = Qwen3CloneSpeechService(config).build_voiceover_service(audio_directory=tmp_path)
    with patch("manim_tutorial.tts.qwen.subprocess.run") as run:
        service.generate_from_text("Beat one.")
    run.assert_called_once()
    command = run.call_args.args[0]
    assert command[0] == "ffmpeg"
    assert "atempo=1.15" in command
