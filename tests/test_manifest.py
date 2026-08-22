import json
from pathlib import Path

from manim_tutorial.render.artifacts import create_artifact_paths
from manim_tutorial.render.manifest import write_timeline


def test_artifact_paths_and_timeline(tmp_path: Path):
    artifacts = create_artifact_paths(tmp_path, Path("vectors.py"))
    assert artifacts.video == tmp_path / "vectors" / "video.mp4"
    write_timeline(
        artifacts.timeline,
        scene="Vectors",
        duration=4.5,
        tts={"provider": "qwen3", "voice": "Ryan"},
        beats=[{"end": 2.5}],
    )
    assert json.loads(artifacts.timeline.read_text())["duration"] == 4.5
