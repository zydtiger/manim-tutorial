from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from .errors import ConfigurationValidationError, ManimTutorialConfigError
from .models import CaptionsConfig, OutputConfig, RenderConfig, TTSConfig, TutorialConfig

CONFIG_ENV = "MANIM_TUTORIAL_CONFIG"
_TTS_SCHEMAS: dict[str, dict[str, type]] = {
    "qwen3": {
        "provider": str,
        "model": str,
        "voice": str,
        "language": str,
        "device": str,
        "rate": float,
    },
    "qwen3-clone": {
        "provider": str,
        "model": str,
        "ref_audio": str,
        "ref_text": str,
        "language": str,
        "device": str,
        "rate": float,
    },
}
_OTHER_SCHEMA: dict[str, dict[str, type]] = {
    "captions": {"enabled": bool, "burn": bool, "font_size": int},
    "render": {"width": int, "height": int, "fps": int},
    "output": {"directory": str},
}


def _format_errors(path: Path, errors: list[str]) -> ConfigurationValidationError:
    return ConfigurationValidationError(f"Invalid configuration: {path}\n\n" + "\n".join(errors))


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
    tts_raw = raw.get("tts")
    provider_value = tts_raw.get("provider") if isinstance(tts_raw, dict) else None
    provider: str = provider_value if isinstance(provider_value, str) else ""
    # An unrecognized (or missing) provider still needs a deterministic schema
    # to structurally validate against; fall back to qwen3 so missing/unknown
    # field reporting stays well-defined, and reject the provider value below.
    tts_schema = _TTS_SCHEMAS.get(provider, _TTS_SCHEMAS["qwen3"])
    schema: dict[str, dict[str, type]] = {"tts": tts_schema, **_OTHER_SCHEMA}
    missing: list[str] = []
    extras: list[str] = []
    type_errors: list[str] = []
    for table, fields in schema.items():
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
    extras.extend(key for key in raw if key not in schema)
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
    if provider not in _TTS_SCHEMAS:
        values.append("  tts.provider: must be one of qwen3, qwen3-clone")
    if tts["device"] not in {"auto", "cuda", "cpu"}:
        values.append("  tts.device: must be one of auto, cuda, cpu")
    if not 0.5 <= tts["rate"] <= 2.0:
        values.append("  tts.rate: must be between 0.5 and 2.0")
    for field in ("model", "language"):
        if not tts[field].strip():
            values.append(f"  tts.{field}: must not be empty")
    ref_audio_path: Path | None = None
    if provider == "qwen3-clone":
        if not tts["ref_text"].strip():
            values.append("  tts.ref_text: must not be empty")
        if not tts["ref_audio"].strip():
            values.append("  tts.ref_audio: must not be empty")
        else:
            candidate = Path(tts["ref_audio"]).expanduser()
            if not candidate.is_absolute():
                candidate = source.parent / candidate
            candidate = candidate.resolve()
            if not candidate.is_file():
                values.append(f"  tts.ref_audio: file does not exist: {candidate}")
            else:
                ref_audio_path = candidate
    else:
        if not tts["voice"].strip():
            values.append("  tts.voice: must not be empty")
    for section, key in (
        (captions, "font_size"),
        (render, "width"),
        (render, "height"),
        (render, "fps"),
    ):
        if section[key] <= 0:
            name = next(
                name for name, fields in schema.items() if key in fields and fields[key] is int
            )
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
    if provider == "qwen3-clone":
        tts_config = TTSConfig(
            provider=provider,
            model=tts["model"],
            voice=None,
            language=tts["language"],
            device=tts["device"],
            rate=tts["rate"],
            ref_audio=ref_audio_path,
            ref_text=tts["ref_text"],
        )
    else:
        tts_config = TTSConfig(
            provider=provider,
            model=tts["model"],
            voice=tts["voice"],
            language=tts["language"],
            device=tts["device"],
            rate=tts["rate"],
        )
    return TutorialConfig(
        tts=tts_config,
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
