from pathlib import Path

import pytest

from manim_tutorial.cli.main import main
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
