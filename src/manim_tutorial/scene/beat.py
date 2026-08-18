from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialBeat:
    """Timing exposed to a tutorial while a narration beat is active."""

    duration: float
