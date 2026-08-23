# manim-tutorial

`manim-tutorial` is a small explicit-config runtime for narrated mathematical
videos built with Manim, Manim Voiceover, and local Qwen3-TTS. It pairs normal
Python tutorial code with a reusable `TutorialScene` and beat-level timeline,
subtitle, and artifact handling.

This repository is intended to remain independent of private tutorial content.

## Install

Python 3.11 through 3.13 are supported. Python 3.12 is the pinned and
recommended local development version:

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

### TTS providers

`tts.provider` selects one of two mutually exclusive `[tts]` schemas:

- `qwen3` synthesizes narration with a preset speaker from a CustomVoice
  checkpoint. Required fields: `provider`, `model`, `voice`, `language`,
  `device`, `rate`.
- `qwen3-clone` synthesizes narration in a cloned voice from a personal
  reference recording, using a Base checkpoint. Required fields: `provider`,
  `model`, `ref_audio`, `ref_text`, `language`, `device`, `rate`; there is no
  `voice` field under this provider.

`Qwen/Qwen3-TTS-12Hz-0.6B-Base` is a reasonable starting checkpoint for
`qwen3-clone`; `Qwen/Qwen3-TTS-12Hz-1.7B-Base` is a configuration-only quality
upgrade (same fields, a larger model).

`ref_audio` points at a personal reference recording kept outside this
repository, for example `~/voices/narrator.wav`; a relative path resolves
against the configuration file's directory. Record roughly 10-20 seconds of
clean, single-speaker speech with minimal background noise and reverb, and
set `ref_text` to its exact transcript, punctuation and casing included. The
voice clone prompt is built once per render and reused for every beat. Never
commit a reference recording, its transcript, or a machine-local path into
this repository; documented examples use placeholder paths only.

The voiceover cache identity and the `timeline.json` manifest identify
`qwen3-clone` narration by a sha256 hash of the reference audio's bytes,
never by its local path.

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
            self.play(GrowArrow(vector), run_time=min(0.8, beat.duration))
```

Animations use concise, independent timings. When an animation finishes before
its narration, the beat holds the completed visual until the voiceover ends.
`tts.rate` controls pitch-preserving narration speed; `1.15` is a useful brisk
starting point.

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

## License

`manim-tutorial` is released under the [MIT License](LICENSE).
