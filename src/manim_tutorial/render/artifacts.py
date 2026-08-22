from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config.errors import ManimTutorialConfigError

ARTIFACT_OWNER_FILENAME = ".manim-tutorial-owner.json"


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path
    video: Path
    subtitles: Path
    timeline: Path
    audio: Path
    captioned_video: Path


def create_artifact_paths(output_directory: Path, tutorial_file: Path) -> ArtifactPaths:
    root = output_directory / tutorial_file.stem
    return ArtifactPaths(
        root=root,
        video=root / "video.mp4",
        subtitles=root / "subtitles.srt",
        timeline=root / "timeline.json",
        audio=root / "audio",
        captioned_video=root / "video_captioned.mp4",
    )


def ensure_artifact_owner(artifacts: ArtifactPaths, *, tutorial: Path, scene: str) -> None:
    """Claim an artifact root or verify that this render already owns it."""
    expected = {"scene": scene, "tutorial": str(tutorial.resolve())}
    marker = artifacts.root / ARTIFACT_OWNER_FILENAME
    if artifacts.root.exists() and marker.exists():
        try:
            actual = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManimTutorialConfigError(f"Invalid artifact ownership marker: {marker}") from exc
        if actual != expected:
            raise ManimTutorialConfigError(
                f"Artifact directory is owned by a different tutorial or scene: {artifacts.root}\n"
                "Choose a distinct output.directory or rename one tutorial source."
            )
        return
    if artifacts.root.exists() and any(artifacts.root.iterdir()):
        raise ManimTutorialConfigError(
            f"Artifact directory has no manim-tutorial ownership marker: {artifacts.root}\n"
            "Choose a distinct output.directory or clear this directory deliberately."
        )
    artifacts.root.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(expected, sort_keys=True) + "\n", encoding="utf-8")
