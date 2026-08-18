from pathlib import Path

from manim_tutorial.captions import format_timestamp, write_srt


def test_srt_timing_and_caption(tmp_path: Path):
    target = tmp_path / "subtitles.srt"
    write_srt(target, [{"start": 1.2, "end": 3.456, "caption": "A short\ncaption."}])
    assert format_timestamp(3661.001) == "01:01:01,001"
    assert target.read_text() == "1\n00:00:01,200 --> 00:00:03,456\nA short caption.\n"
