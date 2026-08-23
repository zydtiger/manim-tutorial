from pathlib import Path

import pytest

from manim_tutorial.config import ConfigurationValidationError, load_config

VALID = """
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "auto"
rate = 1.15
[captions]
enabled = true
burn = true
font_size = 42
[render]
width = 1920
height = 1080
fps = 60
[output]
directory = "output"
"""

CLONE_TTS_BLOCK = """
[tts]
provider = "qwen3-clone"
model = "model"
ref_audio = "{ref_audio}"
ref_text = "Hello, this is my voice."
language = "English"
device = "auto"
rate = 1.15
"""

CLONE_TAIL = """
[captions]
enabled = true
burn = true
font_size = 42
[render]
width = 1920
height = 1080
fps = 60
[output]
directory = "output"
"""


def test_config_requires_all_public_fields_and_resolves_output(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace('language = "English"\n', ""))
    with pytest.raises(ConfigurationValidationError, match=r"tts\.language"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_unknown_fields(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID + "extra = 3\n")
    with pytest.raises(ConfigurationValidationError, match="Unknown fields"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_burn_without_captions(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace("enabled = true", "enabled = false"))
    with pytest.raises(ConfigurationValidationError, match=r"requires captions\.enabled"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_empty_tts_identity_fields(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace('voice = "Ryan"', 'voice = ""'))
    with pytest.raises(ConfigurationValidationError, match=r"tts\.voice: must not be empty"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_out_of_range_tts_rate(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace("rate = 1.15", "rate = 2.5"))
    with pytest.raises(
        ConfigurationValidationError, match=r"tts\.rate: must be between 0\.5 and 2\.0"
    ):
        load_config(path, output_base=tmp_path)


def test_config_loads_valid_clone_provider_with_resolved_absolute_ref_audio(tmp_path: Path):
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake wav bytes")
    path = tmp_path / "tutorial.toml"
    path.write_text(CLONE_TTS_BLOCK.format(ref_audio=ref_audio) + CLONE_TAIL)
    config = load_config(path, output_base=tmp_path)
    assert config.tts.provider == "qwen3-clone"
    assert config.tts.voice is None
    assert config.tts.ref_audio == ref_audio.resolve()
    assert config.tts.ref_audio.is_absolute()
    assert config.tts.ref_text == "Hello, this is my voice."


def test_config_rejects_voice_field_under_clone_provider(tmp_path: Path):
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake wav bytes")
    path = tmp_path / "tutorial.toml"
    path.write_text(
        CLONE_TTS_BLOCK.format(ref_audio=ref_audio).replace(
            "rate = 1.15\n", 'rate = 1.15\nvoice = "Ryan"\n'
        )
        + CLONE_TAIL
    )
    with pytest.raises(ConfigurationValidationError, match=r"(?s)Unknown fields.*tts\.voice"):
        load_config(path, output_base=tmp_path)


def test_config_reports_missing_clone_fields(tmp_path: Path):
    ref_audio = tmp_path / "reference.wav"
    ref_audio.write_bytes(b"fake wav bytes")
    path = tmp_path / "tutorial.toml"
    tts_block = CLONE_TTS_BLOCK.format(ref_audio=ref_audio).replace(
        'ref_text = "Hello, this is my voice."\n', ""
    )
    path.write_text(tts_block + CLONE_TAIL)
    with pytest.raises(
        ConfigurationValidationError, match=r"(?s)Missing required fields.*tts\.ref_text"
    ):
        load_config(path, output_base=tmp_path)


def test_config_rejects_missing_reference_audio_file(tmp_path: Path):
    missing = tmp_path / "does-not-exist.wav"
    path = tmp_path / "tutorial.toml"
    path.write_text(CLONE_TTS_BLOCK.format(ref_audio=missing) + CLONE_TAIL)
    with pytest.raises(ConfigurationValidationError, match=r"tts\.ref_audio: file does not exist"):
        load_config(path, output_base=tmp_path)


def test_config_resolves_relative_ref_audio_against_config_directory(tmp_path: Path):
    config_dir = tmp_path / "project"
    config_dir.mkdir()
    ref_audio = config_dir / "voices" / "narrator.wav"
    ref_audio.parent.mkdir(parents=True)
    ref_audio.write_bytes(b"fake wav bytes")
    path = config_dir / "tutorial.toml"
    path.write_text(CLONE_TTS_BLOCK.format(ref_audio="voices/narrator.wav") + CLONE_TAIL)
    config = load_config(path, output_base=tmp_path)
    assert config.tts.ref_audio == ref_audio.resolve()


def test_config_rejects_unknown_provider_value(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace('provider = "qwen3"', 'provider = "unknown"'))
    with pytest.raises(
        ConfigurationValidationError, match=r"tts\.provider: must be one of qwen3, qwen3-clone"
    ):
        load_config(path, output_base=tmp_path)
