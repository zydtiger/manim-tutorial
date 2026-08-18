from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping


def format_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_srt(path: Path, beats: Iterable[Mapping[str, object]]) -> None:
    entries: list[str] = []
    for index, beat in enumerate(beats, start=1):
        start = float(beat["start"])
        end = max(float(beat["end"]), start + 0.001)
        caption = " ".join(str(beat["caption"]).splitlines())
        entries.append(f"{index}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{caption}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(entries), encoding="utf-8")
