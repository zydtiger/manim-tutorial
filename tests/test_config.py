from pathlib import Path

import pytest

from manim_tutorial.config import ConfigurationValidationError, load_config


VALID = '''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "auto"
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
'''


def test_config_requires_all_public_fields_and_resolves_output(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace('language = "English"\n', ""))
    with pytest.raises(ConfigurationValidationError, match="tts.language"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_unknown_fields(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID + "extra = 3\n")
    with pytest.raises(ConfigurationValidationError, match="Unknown fields"):
        load_config(path, output_base=tmp_path)


def test_config_rejects_burn_without_captions(tmp_path: Path):
    path = tmp_path / "tutorial.toml"
    path.write_text(VALID.replace("enabled = true", "enabled = false"))
    with pytest.raises(ConfigurationValidationError, match="requires captions.enabled"):
        load_config(path, output_base=tmp_path)
