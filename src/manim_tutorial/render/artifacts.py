from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
