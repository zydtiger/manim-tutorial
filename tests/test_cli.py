import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from manim_tutorial.cli.main import main
from manim_tutorial.cli import check as check_module
from manim_tutorial.config.models import CaptionsConfig, OutputConfig, RenderConfig, TTSConfig, TutorialConfig
from manim_tutorial.render.pipeline import discover_tutorial_scenes, select_scene


def test_cli_requires_explicit_config(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["check"])
    assert exit_info.value.code == 2
    assert "--config is required" in capsys.readouterr().err


def test_scene_discovery_requires_choice_for_multiple_scenes(tmp_path: Path):
    source = tmp_path / "lesson.py"
    source.write_text("class One(TutorialScene): pass\nclass Two(TutorialScene): pass\n")
    assert discover_tutorial_scenes(source) == ["One", "Two"]
    with pytest.raises(Exception, match="More than one"):
        select_scene(source, None)
    assert select_scene(source, "One") == "One"


def _config_with_captions(*, enabled: bool, burn: bool) -> TutorialConfig:
    return TutorialConfig(
        tts=TTSConfig("qwen3", "model", "Ryan", "English", "cpu"),
        captions=CaptionsConfig(enabled, burn, 42),
        render=RenderConfig(640, 480, 15),
        output=OutputConfig(Path("output")),
        source_path=Path("tutorial.toml"),
    )


def test_check_treats_disabled_captions_as_ready(monkeypatch):
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setattr(check_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(check_module.shutil, "which", lambda _: "/usr/bin/tool")
    monkeypatch.setattr(check_module, "sys", SimpleNamespace(version="3.12", executable="python"))
    ready, lines = check_module.check_environment(_config_with_captions(enabled=False, burn=False))
    assert ready is True
    assert not any("SRT support" in line or "subtitle support" in line for line in lines)


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
