import sys
from pathlib import Path

from manim_tutorial.config import load_config
from manim_tutorial.render.pipeline import manim_command


def test_manim_command_uses_current_python_and_explicit_render_fields(tmp_path: Path):
    config_file = tmp_path / "tutorial.toml"
    config_file.write_text('''
[tts]
provider = "qwen3"
model = "model"
voice = "Ryan"
language = "English"
device = "cpu"
[captions]
enabled = true
burn = false
font_size = 42
[render]
width = 640
height = 480
fps = 15
[output]
directory = "output"
''')
    config = load_config(config_file, output_base=tmp_path)
    command = manim_command(
        tutorial=tmp_path / "lesson.py", scene="Lesson", config=config, media_dir=tmp_path / "stage"
    )
    assert command[:4] == [sys.executable, "-m", "manim", "render"]
    assert command[4:6] == [str(tmp_path / "lesson.py"), "Lesson"]
    assert "640,480" in command and "15" in command and "--media_dir" in command
