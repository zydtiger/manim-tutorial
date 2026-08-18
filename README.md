# manim-tutorial

`manim-tutorial` is a small explicit-config runtime for narrated mathematical
videos built with Manim, Manim Voiceover, and local Qwen3-TTS. It pairs normal
Python tutorial code with a reusable `TutorialScene` and beat-level timeline,
subtitle, and artifact handling.

This repository is intended to remain independent of private tutorial content.

## Install

Use Python 3.12 with uv:

```bash
uv sync --python 3.12
```

The first real Qwen render downloads the configured model. `check` deliberately
does not download or load model weights.

## Configuration

Copy [tutorial.toml.example](tutorial.toml.example) into a content project and
fill every field. The schema is exact: all documented fields are required and
unknown fields are rejected. There is no config discovery, global config, or
CLI override for render behavior.

```bash
manim-tutorial check --config configs/youtube.toml
manim-tutorial render projects/linear-algebra/lessons/vector_rotation.py \
  --scene VectorRotation --config configs/youtube.toml
```

Relative `output.directory` paths are resolved against the directory from which
the command is run. The CLI resolves `--config` to an absolute path before it
launches Manim.

`check` verifies installed runtime prerequisites without downloads. It reports
missing Manim, Qwen3-TTS, FFmpeg, LaTeX/dvisvgm, or an unavailable requested
CUDA device as non-ready conditions.

## Tutorial API

Tutorial files are ordinary Manim Python. They do not contain configuration
paths, TTS initialization, or FFmpeg plumbing.

Tutorial source is executable Python. Render only tutorial files you trust.

```python
from manim import Arrow, GrowArrow, ORIGIN, RIGHT
from manim_tutorial import TutorialScene


class PointRight(TutorialScene):
    def construct(self):
        vector = Arrow(ORIGIN, 3 * RIGHT)
        with self.beat(
            speech="Here is a vector pointing right.",
            caption="A vector pointing right.",
        ) as beat:
            self.play(GrowArrow(vector), run_time=beat.duration)
```

Always render a `TutorialScene` through `manim-tutorial render`. Direct Manim
invocation fails clearly because the required explicit configuration transport
is absent.

## Artifacts

For `output.directory = "./output"` and `vector_rotation.py`, a render writes:

```text
output/vector_rotation/
  video.mp4
  video_captioned.mp4       # only when captions.burn = true
  subtitles.srt             # only when captions.enabled = true
  timeline.json
  audio/
```

Each `beat` records `speech`, `caption`, and narration timing. Captions are
intentionally allowed to be shorter than speech. Caption burning uses FFmpeg's
`subtitles` filter (libass) on Linux in V1.

Artifact directories are keyed by tutorial filename stem. A hidden marker binds
each directory to the resolved tutorial source and scene, so two different
`vectors.py` files cannot overwrite one another under the same output directory.
Use a distinct `output.directory` or rename one source if the CLI reports an
artifact ownership collision.

## Development

```bash
uv run pytest
```

Unit tests do not require GPU hardware, a Qwen download, or a full Manim
render. A real end-to-end render additionally needs Manim's system dependencies
(including LaTeX), Qwen weights, and a working local TTS setup.
