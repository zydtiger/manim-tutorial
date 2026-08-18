from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys

from ..config.models import TutorialConfig


def _status(label: str, ok: bool, detail: str = "") -> tuple[bool, str]:
    return ok, f"  {'✓' if ok else '✗'} {label}{f': {detail}' if detail else ''}"


def _info(label: str, detail: str) -> tuple[bool, str]:
    """Report a configured request that cannot be verified without a download."""
    return True, f"  • {label}: {detail}"


def _supported_python(version_info: tuple[int, int]) -> bool:
    return version_info >= (3, 11)


def _has_ffmpeg_subtitles_filter() -> bool:
    """Check the libass-backed filter needed by the burn pipeline."""
    if shutil.which("ffmpeg") is None:
        return False
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-h", "filter=subtitles"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def check_environment(config: TutorialConfig) -> tuple[bool, list[str]]:
    results: list[tuple[bool, str]] = []
    results.append(_status("Python", _supported_python(sys.version_info[:2]), sys.executable))
    results.append(_status("Manim", importlib.util.find_spec("manim") is not None))
    results.append(_status("FFmpeg", shutil.which("ffmpeg") is not None))
    results.append(_status("LaTeX", shutil.which("latex") is not None and shutil.which("dvisvgm") is not None))
    results.append(_status("provider", True, config.tts.provider))
    results.append(_status("Qwen3 TTS package", importlib.util.find_spec("qwen_tts") is not None))
    torch_spec = importlib.util.find_spec("torch")
    device_detail = config.tts.device
    device_ok = torch_spec is not None
    if torch_spec is not None:
        import torch

        resolved = "cuda" if config.tts.device == "auto" and torch.cuda.is_available() else config.tts.device
        device_detail = f"requested {config.tts.device}, resolved {resolved}"
        device_ok = resolved != "cuda" or torch.cuda.is_available()
    results.append(_status("TTS device", device_ok, device_detail))
    results.append(_info("requested model", f"{config.tts.model} (unverified offline; downloads on first render)"))
    results.append(_info("requested voice", f"{config.tts.voice} (unverified until the model is available)"))
    if config.captions.enabled:
        results.append(_status("SRT support", True))
    if config.captions.burn:
        results.append(_status("FFmpeg subtitle support", _has_ffmpeg_subtitles_filter()))
    results.append(_status("render", True, f"{config.render.width}x{config.render.height} @ {config.render.fps} FPS"))
    return all(ok for ok, _ in results), [line for _, line in results]
