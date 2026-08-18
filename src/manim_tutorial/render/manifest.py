from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_timeline(
    path: Path, *, scene: str, duration: float, tts: dict[str, str], beats: list[dict[str, Any]]
) -> None:
    """Write beat timing plus the full rendered scene duration."""
    payload = {"scene": scene, "duration": duration, "tts": tts, "beats": beats}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
