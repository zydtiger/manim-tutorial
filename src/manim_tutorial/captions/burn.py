from __future__ import annotations

import subprocess
from pathlib import Path


def _escape_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def burn_captions(*, video: Path, subtitles: Path, output: Path, font_size: int) -> list[str]:
    """Burn SRT captions using FFmpeg/libass and return the invoked command."""
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_value = f"subtitles='{_escape_filter_path(subtitles)}':force_style='Fontsize={font_size}'"
    command = [
        "ffmpeg", "-y", "-i", str(video), "-vf", filter_value,
        "-c:a", "copy", str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return command
