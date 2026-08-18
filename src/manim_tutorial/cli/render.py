from __future__ import annotations

from pathlib import Path

from ..config.models import TutorialConfig
from ..render.pipeline import render_tutorial


def execute_render(tutorial: str, config: TutorialConfig, scene: str | None):
    return render_tutorial(tutorial=Path(tutorial), config=config, scene=scene)
