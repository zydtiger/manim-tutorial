from pathlib import Path
from unittest.mock import patch

from manim_tutorial.captions.burn import burn_captions


def test_burn_invokes_ffmpeg(tmp_path: Path):
    with patch("manim_tutorial.captions.burn.subprocess.run") as run:
        command = burn_captions(
            video=tmp_path / "video.mp4", subtitles=tmp_path / "subtitles.srt",
            output=tmp_path / "captioned.mp4", font_size=42,
        )
    assert command[0] == "ffmpeg"
    assert "Fontsize=42" in command[5]
    run.assert_called_once()
