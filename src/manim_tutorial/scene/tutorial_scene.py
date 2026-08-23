from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from manim_voiceover import VoiceoverScene

from ..config import ManimTutorialConfigError, load_config_from_environment
from ..render.manifest import write_timeline
from ..tts import create_speech_service, timeline_identity
from .beat import TutorialBeat

TIMELINE_ENV = "MANIM_TUTORIAL_TIMELINE_PATH"
AUDIO_DIR_ENV = "MANIM_TUTORIAL_AUDIO_DIR"


class TutorialScene(VoiceoverScene):
    """VoiceoverScene configured solely by the rendering CLI's explicit config."""

    def setup(self) -> None:
        super().setup()
        self._tutorial_config = load_config_from_environment()
        timeline_path = os.environ.get(TIMELINE_ENV)
        audio_directory = os.environ.get(AUDIO_DIR_ENV)
        if not timeline_path or not audio_directory:
            raise ManimTutorialConfigError(
                "No manim-tutorial render transport was supplied.\n\n"
                "Render this scene with:\n\n"
                "  manim-tutorial render <tutorial.py> --config <config.toml>"
            )
        self._timeline_path = Path(timeline_path)
        self._audio_directory = Path(audio_directory)
        self._beats: list[dict[str, object]] = []
        self.set_speech_service(
            create_speech_service(self._tutorial_config.tts, audio_directory=self._audio_directory),
            create_subcaption=False,
        )

    @contextmanager
    def beat(self, *, speech: str, caption: str) -> Iterator[TutorialBeat]:
        """Synchronize one visual idea with one narration beat."""
        if not speech.strip():
            raise ValueError("beat speech must not be empty")
        if not caption.strip():
            raise ValueError("beat caption must not be empty")
        with self.voiceover(text=speech, subcaption=caption) as tracker:
            yield TutorialBeat(duration=float(tracker.duration))
        start = float(getattr(tracker, "start_t", self.renderer.time - tracker.duration))
        end = float(getattr(tracker, "end_t", start + tracker.duration))
        self._beats.append(
            {
                "id": len(self._beats) + 1,
                "start": start,
                "end": end,
                "duration": float(tracker.duration),
                "speech": speech,
                "caption": caption,
            }
        )

    def tear_down(self) -> None:
        try:
            write_timeline(
                self._timeline_path,
                scene=self.__class__.__name__,
                duration=float(self.renderer.time),
                tts=timeline_identity(self._tutorial_config.tts),
                beats=self._beats,
            )
        finally:
            super().tear_down()
