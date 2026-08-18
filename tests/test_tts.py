import pytest

from manim_tutorial.config.models import TTSConfig
from manim_tutorial.tts.qwen import build_voiceover_input_data, resolve_device


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
    )
    assert build_voiceover_input_data("Explain eigenvectors.", config) == {
        "input_text": "Explain eigenvectors.",
        "service": "qwen3",
        "config": {
            "model": "Qwen/model",
            "voice": "Ryan",
            "language": "English",
            "device": "auto",
        },
    }
