from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_timeline(path: Path, *, scene: str, tts: dict[str, str], beats: list[dict[str, Any]]) -> None:
    duration = max((float(beat["end"]) for beat in beats), default=0.0)
    payload = {"scene": scene, "duration": duration, "tts": tts, "beats": beats}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
