import builtins
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from manim_tutorial.cli import check as check_module
from manim_tutorial.cli.main import main
from manim_tutorial.config.models import (
    CaptionsConfig,
    OutputConfig,
    RenderConfig,
    TTSConfig,
    TutorialConfig,
)
from manim_tutorial.render.pipeline import discover_tutorial_scenes, select_scene


def test_cli_requires_explicit_config(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["check"])
    assert exit_info.value.code == 2
    assert "--config is required" in capsys.readouterr().err


def test_module_entrypoint_propagates_cli_exit_code():
    completed = subprocess.run(
        [sys.executable, "-m", "manim_tutorial", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "--config is required" in completed.stderr


def test_scene_discovery_requires_choice_for_multiple_scenes(tmp_path: Path):
    source = tmp_path / "lesson.py"
    source.write_text("class One(TutorialScene): pass\nclass Two(TutorialScene): pass\n")
    assert discover_tutorial_scenes(source) == ["One", "Two"]
    with pytest.raises(Exception, match="More than one"):
        select_scene(source, None)
    assert select_scene(source, "One") == "One"


def _config_with_captions(*, enabled: bool, burn: bool, device: str = "cpu") -> TutorialConfig:
    return TutorialConfig(
        tts=TTSConfig("qwen3", "model", "Ryan", "English", device, 1.15),
        captions=CaptionsConfig(enabled, burn, 42),
        render=RenderConfig(640, 480, 15),
        output=OutputConfig(Path("output")),
        source_path=Path("tutorial.toml"),
    )


def test_check_treats_disabled_captions_as_ready(monkeypatch):
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "qwen_tts", SimpleNamespace(Qwen3TTSModel=object))
    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(check_module.shutil, "which", lambda _: "/usr/bin/tool")
    monkeypatch.setattr(
        check_module, "sys", SimpleNamespace(version_info=(3, 12), executable="python")
    )
    ready, lines = check_module.check_environment(_config_with_captions(enabled=False, burn=False))
    assert ready is True
    assert not any("SRT support" in line or "subtitle support" in line for line in lines)
    assert any("✓ provider: qwen3" in line for line in lines)
    assert any("• requested model: model (unverified offline" in line for line in lines)
    assert any("• requested voice: Ryan (unverified" in line for line in lines)


def test_python_version_check_is_numeric():
    assert check_module._supported_python((3, 9)) is False
    assert check_module._supported_python((3, 10)) is False
    assert check_module._supported_python((3, 11)) is True


def test_check_reports_auto_device_cpu_fallback(monkeypatch):
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "qwen_tts", SimpleNamespace(Qwen3TTSModel=object))
    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(check_module.shutil, "which", lambda _: "/usr/bin/tool")
    monkeypatch.setattr(
        check_module, "sys", SimpleNamespace(version_info=(3, 12), executable="python")
    )
    ready, lines = check_module.check_environment(
        _config_with_captions(enabled=False, burn=False, device="auto")
    )
    assert ready is True
    assert any("TTS device: requested auto, resolved cpu" in line for line in lines)


def test_check_reports_broken_torch_without_traceback(monkeypatch):
    original_import = builtins.__import__

    def broken_torch_import(name, *args, **kwargs):
        if name == "torch":
            raise OSError("missing CUDA library")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(check_module.shutil, "which", lambda _: "/usr/bin/tool")
    monkeypatch.setattr(
        check_module, "sys", SimpleNamespace(version_info=(3, 12), executable="python")
    )
    monkeypatch.setattr(builtins, "__import__", broken_torch_import)
    ready, lines = check_module.check_environment(_config_with_captions(enabled=False, burn=False))
    assert ready is False
    assert any("cannot import or probe torch: missing CUDA library" in line for line in lines)


def test_qwen_probe_accepts_required_api_without_model_loading(monkeypatch):
    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setitem(sys.modules, "qwen_tts", SimpleNamespace(Qwen3TTSModel=object))
    assert check_module._probe_qwen_tts() == (True, "imported")


def test_qwen_probe_reports_broken_import(monkeypatch):
    original_import = builtins.__import__

    def broken_qwen_import(name, *args, **kwargs):
        if name == "qwen_tts":
            raise OSError("missing runtime library")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(builtins, "__import__", broken_qwen_import)
    ok, detail = check_module._probe_qwen_tts()
    assert ok is False
    assert detail == "cannot import Qwen3TTSModel: missing runtime library"


def test_check_requires_ffmpeg_subtitles_filter_for_burn(monkeypatch):
    monkeypatch.setattr(check_module.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(
        check_module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1)
    )
    assert check_module._has_ffmpeg_subtitles_filter() is False
    monkeypatch.setattr(
        check_module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )
    assert check_module._has_ffmpeg_subtitles_filter() is True
