from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TTSConfig:
    provider: str
    model: str
    voice: str
    language: str
    device: str
    rate: float


@dataclass(frozen=True)
class CaptionsConfig:
    enabled: bool
    burn: bool
    font_size: int


@dataclass(frozen=True)
class RenderConfig:
    width: int
    height: int
    fps: int


@dataclass(frozen=True)
class OutputConfig:
    directory: Path


@dataclass(frozen=True)
class TutorialConfig:
    tts: TTSConfig
    captions: CaptionsConfig
    render: RenderConfig
    output: OutputConfig
    source_path: Path
