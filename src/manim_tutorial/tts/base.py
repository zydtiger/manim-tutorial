from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TutorialSpeechService(ABC):
    """Small factory-facing protocol kept separate from tutorial source."""

    @abstractmethod
    def build_voiceover_service(self, *, audio_directory: Path):
        """Return a Manim Voiceover SpeechService instance."""
