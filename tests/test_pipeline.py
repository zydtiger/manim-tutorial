import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from manim_tutorial.config import ManimTutorialConfigError
from manim_tutorial.config import load_config
from manim_tutorial.render import create_artifact_paths
from manim_tutorial.render.artifacts import ARTIFACT_OWNER_FILENAME
from manim_tutorial.render.pipeline import manim_command, render_tutorial


def test_manim_command_uses_current_python_and_explicit_render_fields(tmp_path: Path):
    config_file = tmp_path / "tutorial.toml"
    config_file.write_text('''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "cpu"
[captions]
enabled = true
burn = false
font_size = 42
[render]
width = 640
height = 480
fps = 15
[output]
directory = "output"
''')
    config = load_config(config_file, output_base=tmp_path)
    command = manim_command(
        tutorial=tmp_path / "lesson.py", scene="Lesson", config=config, media_dir=tmp_path / "stage"
    )
    assert command[:4] == [sys.executable, "-m", "manim", "render"]
    assert command[4:6] == [str(tmp_path / "lesson.py"), "Lesson"]
    assert "640,480" in command and "15" in command and "--media_dir" in command


def test_successful_rerender_removes_only_stale_runtime_artifacts(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "tutorial.toml"
    config_file.write_text('''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "cpu"
[captions]
enabled = false
burn = false
font_size = 42
[render]
width = 640
height = 480
fps = 15
[output]
directory = "output"
''')
    config = load_config(config_file, output_base=tmp_path)
    tutorial = tmp_path / "lesson.py"
    tutorial.write_text("class Lesson: pass\n")
    artifacts = create_artifact_paths(config.output.directory, tutorial)
    artifacts.audio.mkdir(parents=True)
    (artifacts.root / ARTIFACT_OWNER_FILENAME).write_text(
        json.dumps({"scene": "Lesson", "tutorial": str(tutorial.resolve())}, sort_keys=True) + "\n"
    )
    artifacts.subtitles.write_text("stale")
    artifacts.captioned_video.write_text("stale")
    (artifacts.audio / "beat_001.wav").write_text("current")
    (artifacts.audio / "beat_002.wav").write_text("stale")
    (artifacts.audio / "user.wav").write_text("preserve")
    (artifacts.root / "notes.txt").write_text("preserve")

    def fake_manim(command, *, env, **kwargs):
        stage = Path(command[command.index("--media_dir") + 1])
        video = stage / "videos" / "video.mp4"
        video.parent.mkdir(parents=True)
        video.write_text("new video")
        Path(env["MANIM_TUTORIAL_TIMELINE_PATH"]).write_text(
            json.dumps({
                "scene": "Lesson", "duration": 1, "tts": {"provider": "qwen3", "voice": "Ryan"},
                "beats": [{"id": 1, "start": 0, "end": 1, "duration": 1, "speech": "One", "caption": "One"}],
            })
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("manim_tutorial.render.pipeline.subprocess.run", fake_manim)
    render_tutorial(tutorial=tutorial, config=config, scene="Lesson")

    assert not artifacts.subtitles.exists()
    assert not artifacts.captioned_video.exists()
    assert (artifacts.audio / "beat_001.wav").exists()
    assert not (artifacts.audio / "beat_002.wav").exists()
    assert (artifacts.audio / "user.wav").exists()
    assert (artifacts.root / "notes.txt").exists()


def test_same_owner_can_rerender_but_same_stem_collision_fails_before_manim(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "tutorial.toml"
    config_file.write_text('''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "cpu"
[captions]
enabled = false
burn = false
font_size = 42
[render]
width = 640
height = 480
fps = 15
[output]
directory = "output"
''')
    config = load_config(config_file, output_base=tmp_path)
    first = tmp_path / "first" / "lesson.py"
    second = tmp_path / "second" / "lesson.py"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("class Lesson: pass\n")
    second.write_text("class Lesson: pass\n")
    calls = []

    def fake_manim(command, *, env, **kwargs):
        calls.append(command)
        stage = Path(command[command.index("--media_dir") + 1])
        video = stage / "videos" / "video.mp4"
        video.parent.mkdir(parents=True)
        video.write_text("video")
        Path(env["MANIM_TUTORIAL_TIMELINE_PATH"]).write_text(
            json.dumps({
                "scene": "Lesson", "duration": 1, "tts": {"provider": "qwen3", "voice": "Ryan"},
                "beats": [{"id": 1, "start": 0, "end": 1, "duration": 1, "speech": "One", "caption": "One"}],
            })
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("manim_tutorial.render.pipeline.subprocess.run", fake_manim)
    render_tutorial(tutorial=first, config=config, scene="Lesson")
    render_tutorial(tutorial=first, config=config, scene="Lesson")
    with pytest.raises(ManimTutorialConfigError, match="owned by a different tutorial"):
        render_tutorial(tutorial=first, config=config, scene="OtherScene")
    with pytest.raises(ManimTutorialConfigError, match="owned by a different tutorial"):
        render_tutorial(tutorial=second, config=config, scene="Lesson")
    assert len(calls) == 2


def test_render_does_not_reuse_previous_timeline_when_scene_writes_none(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "tutorial.toml"
    config_file.write_text('''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "cpu"
[captions]
enabled = false
burn = false
font_size = 42
[render]
width = 640
height = 480
fps = 15
[output]
directory = "output"
''')
    config = load_config(config_file, output_base=tmp_path)
    tutorial = tmp_path / "lesson.py"
    tutorial.write_text("class OrdinaryScene: pass\n")
    artifacts = create_artifact_paths(config.output.directory, tutorial)
    artifacts.root.mkdir(parents=True)
    (artifacts.root / ARTIFACT_OWNER_FILENAME).write_text(
        json.dumps({"scene": "OrdinaryScene", "tutorial": str(tutorial.resolve())}, sort_keys=True) + "\n"
    )
    artifacts.timeline.write_text(json.dumps({"scene": "Old", "beats": [{"caption": "stale"}]}))

    def fake_manim(command, **kwargs):
        stage = Path(command[command.index("--media_dir") + 1])
        video = stage / "videos" / "video.mp4"
        video.parent.mkdir(parents=True)
        video.write_text("new video")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("manim_tutorial.render.pipeline.subprocess.run", fake_manim)
    with pytest.raises(ManimTutorialConfigError, match="fresh timeline"):
        render_tutorial(tutorial=tutorial, config=config, scene="OrdinaryScene")
    assert json.loads(artifacts.timeline.read_text())["scene"] == "Old"
