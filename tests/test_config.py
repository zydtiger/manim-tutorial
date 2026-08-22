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
