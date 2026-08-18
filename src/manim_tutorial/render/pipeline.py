from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..captions import burn_captions, write_srt
from ..config import CONFIG_ENV, ManimTutorialConfigError, TutorialConfig
from .artifacts import ArtifactPaths, create_artifact_paths

TIMELINE_ENV = "MANIM_TUTORIAL_TIMELINE_PATH"
AUDIO_DIR_ENV = "MANIM_TUTORIAL_AUDIO_DIR"


def discover_tutorial_scenes(tutorial: Path) -> list[str]:
    try:
        tree = ast.parse(tutorial.read_text(encoding="utf-8"), filename=str(tutorial))
    except (OSError, SyntaxError) as exc:
        raise ManimTutorialConfigError(f"Cannot parse tutorial source: {tutorial}\n{exc}") from exc
    names: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "TutorialScene":
                names.append(node.name)
            elif isinstance(base, ast.Attribute) and base.attr == "TutorialScene":
                names.append(node.name)
    return names


def select_scene(tutorial: Path, requested_scene: str | None) -> str:
    if requested_scene:
        return requested_scene
    scenes = discover_tutorial_scenes(tutorial)
    if len(scenes) == 1:
        return scenes[0]
    if not scenes:
        raise ManimTutorialConfigError(
            "No TutorialScene subclass was found. Pass --scene for a compatible scene class."
        )
    raise ManimTutorialConfigError(
        "More than one TutorialScene subclass was found. Pass --scene <SceneClassName>."
    )


def manim_command(*, tutorial: Path, scene: str, config: TutorialConfig, media_dir: Path) -> list[str]:
    return [
        sys.executable, "-m", "manim", "render", str(tutorial), scene,
        "--resolution", f"{config.render.width},{config.render.height}",
        "--fps", str(config.render.fps),
        "--media_dir", str(media_dir), "--output_file", "video",
    ]


def _find_video(media_dir: Path) -> Path:
    matches = list(media_dir.rglob("video.mp4"))
    if len(matches) != 1:
        raise ManimTutorialConfigError(
            f"Manim did not produce exactly one video.mp4 artifact under {media_dir}."
        )
    return matches[0]


def _remove_stale_artifacts(artifacts: ArtifactPaths, *, captions_enabled: bool, burn_captions_enabled: bool, beat_count: int) -> None:
    """Remove only obsolete artifacts whose names are owned by this runtime."""
    if not captions_enabled:
        artifacts.subtitles.unlink(missing_ok=True)
    if not burn_captions_enabled:
        artifacts.captioned_video.unlink(missing_ok=True)
    expected_audio = {f"beat_{index:03}.wav" for index in range(1, beat_count + 1)}
    for audio_file in artifacts.audio.glob("beat_*.wav"):
        if audio_file.name not in expected_audio:
            audio_file.unlink()


def _load_fresh_timeline(path: Path, *, scene: str) -> dict[str, object]:
    if not path.is_file():
        raise ManimTutorialConfigError(
            "Rendered scene did not produce fresh timeline metadata. "
            "Render a TutorialScene with manim-tutorial."
        )
    try:
        timeline = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManimTutorialConfigError("Rendered scene produced invalid timeline metadata.") from exc
    if (
        not isinstance(timeline, dict)
        or timeline.get("scene") != scene
        or not isinstance(timeline.get("duration"), (int, float))
        or not isinstance(timeline.get("tts"), dict)
        or not isinstance(timeline["tts"].get("provider"), str)
        or not isinstance(timeline["tts"].get("voice"), str)
        or not isinstance(timeline.get("beats"), list)
    ):
        raise ManimTutorialConfigError("Rendered scene produced invalid timeline metadata.")
    for beat in timeline["beats"]:
        if not isinstance(beat, dict) or not all(
            key in beat for key in ("id", "start", "end", "duration", "speech", "caption")
        ):
            raise ManimTutorialConfigError("Rendered scene produced invalid timeline metadata.")
    return timeline


def render_tutorial(*, tutorial: Path, config: TutorialConfig, scene: str | None) -> ArtifactPaths:
    tutorial = tutorial.expanduser().resolve()
    if not tutorial.is_file():
        raise ManimTutorialConfigError(f"Tutorial file does not exist: {tutorial}")
    selected_scene = select_scene(tutorial, scene)
    artifacts = create_artifact_paths(config.output.directory, tutorial)
    artifacts.root.mkdir(parents=True, exist_ok=True)
    artifacts.audio.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment[CONFIG_ENV] = str(config.source_path)
    environment[AUDIO_DIR_ENV] = str(artifacts.audio)
    with tempfile.TemporaryDirectory(prefix="manim-stage-", dir=artifacts.root) as stage_name:
        stage = Path(stage_name)
        staged_timeline = stage / "timeline.json"
        environment[TIMELINE_ENV] = str(staged_timeline)
        command = manim_command(tutorial=tutorial, scene=selected_scene, config=config, media_dir=stage)
        try:
            subprocess.run(command, check=True, env=environment)
        except subprocess.CalledProcessError as exc:
            raise ManimTutorialConfigError(f"Manim render failed with exit code {exc.returncode}.") from exc
        staged_video = _find_video(stage)
        timeline = _load_fresh_timeline(staged_timeline, scene=selected_scene)
        shutil.copy2(staged_video, artifacts.video)
        beats = timeline["beats"]
        _remove_stale_artifacts(
            artifacts,
            captions_enabled=config.captions.enabled,
            burn_captions_enabled=config.captions.enabled and config.captions.burn,
            beat_count=len(beats),
        )
        if config.captions.enabled:
            write_srt(artifacts.subtitles, beats)
            if config.captions.burn:
                try:
                    burn_captions(
                        video=artifacts.video,
                        subtitles=artifacts.subtitles,
                        output=artifacts.captioned_video,
                        font_size=config.captions.font_size,
                    )
                except FileNotFoundError as exc:
                    raise ManimTutorialConfigError("FFmpeg is required to burn captions but was not found.") from exc
                except subprocess.CalledProcessError as exc:
                    raise ManimTutorialConfigError("FFmpeg failed while burning captions.") from exc
        shutil.copy2(staged_timeline, artifacts.timeline)
    return artifacts
