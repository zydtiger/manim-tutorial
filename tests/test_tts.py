import pytest

from manim_tutorial.tts.qwen import resolve_device


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
