from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from .errors import ConfigurationValidationError, ManimTutorialConfigError
from .models import CaptionsConfig, OutputConfig, RenderConfig, TTSConfig, TutorialConfig

CONFIG_ENV = "MANIM_TUTORIAL_CONFIG"
_SCHEMA: dict[str, dict[str, type]] = {
    "tts": {"provider": str, "model": str, "voice": str, "language": str, "device": str},
    "captions": {"enabled": bool, "burn": bool, "font_size": int},
    "render": {"width": int, "height": int, "fps": int},
    "output": {"directory": str},
}


def _format_errors(path: Path, errors: list[str]) -> ConfigurationValidationError:
    return ConfigurationValidationError(
        f"Invalid configuration: {path}\n\n" + "\n".join(errors)
    )


def load_config(path: str | Path, *, output_base: Path | None = None) -> TutorialConfig:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ManimTutorialConfigError(f"Configuration file does not exist: {source}")
    try:
        with source.open("rb") as config_file:
            raw: Any = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise ManimTutorialConfigError(f"Invalid TOML configuration: {source}\n{exc}") from exc

    errors: list[str] = []
    if not isinstance(raw, dict):
        raise _format_errors(source, ["Configuration must contain TOML tables."])
    missing: list[str] = []
    extras: list[str] = []
    type_errors: list[str] = []
    for table, fields in _SCHEMA.items():
        value = raw.get(table)
        if not isinstance(value, dict):
            missing.extend(f"{table}.{field}" for field in fields)
            continue
        missing.extend(f"{table}.{field}" for field in fields if field not in value)
        extras.extend(f"{table}.{field}" for field in value if field not in fields)
        for field, expected in fields.items():
            actual = value.get(field)
            if field in value and (type(actual) is not expected):
                type_errors.append(f"  {table}.{field}: expected {expected.__name__}")
    extras.extend(key for key in raw if key not in _SCHEMA)
    if missing:
        errors.append("Missing required fields:\n" + "\n".join(f"  {item}" for item in missing))
    if extras:
        errors.append("Unknown fields:\n" + "\n".join(f"  {item}" for item in extras))
    if type_errors:
        errors.append("Invalid field types:\n" + "\n".join(type_errors))
    if errors:
        raise _format_errors(source, errors)

    tts = raw["tts"]
    captions = raw["captions"]
    render = raw["render"]
    output = raw["output"]
    values: list[str] = []
    if tts["provider"] != "qwen3":
        values.append("  tts.provider: must be 'qwen3'")
    if tts["device"] not in {"auto", "cuda", "cpu"}:
        values.append("  tts.device: must be one of auto, cuda, cpu")
    for field in ("model", "voice", "language"):
        if not tts[field].strip():
            values.append(f"  tts.{field}: must not be empty")
    for section, key in ((captions, "font_size"), (render, "width"), (render, "height"), (render, "fps")):
        if section[key] <= 0:
            name = next(name for name, fields in _SCHEMA.items() if key in fields and fields[key] is int)
            values.append(f"  {name}.{key}: must be greater than zero")
    if not output["directory"].strip():
        values.append("  output.directory: must not be empty")
    if captions["burn"] and not captions["enabled"]:
        values.append("  captions.burn: requires captions.enabled = true")
    if values:
        raise _format_errors(source, ["Invalid field values:\n" + "\n".join(values)])

    base = (output_base or Path.cwd()).resolve()
    output_path = Path(output["directory"]).expanduser()
    if not output_path.is_absolute():
        output_path = base / output_path
    return TutorialConfig(
        tts=TTSConfig(**tts),
        captions=CaptionsConfig(**captions),
        render=RenderConfig(**render),
        output=OutputConfig(directory=output_path.resolve()),
        source_path=source,
    )


def load_config_from_environment() -> TutorialConfig:
    path = os.environ.get(CONFIG_ENV)
    if not path:
        raise ManimTutorialConfigError(
            "No manim-tutorial configuration was supplied.\n\n"
            "Render this scene with:\n\n"
            "  manim-tutorial render <tutorial.py> --config <config.toml>"
        )
    return load_config(path, output_base=Path.cwd())
