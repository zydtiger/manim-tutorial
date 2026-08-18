# CLI reference

Use only the explicit-config commands:

```bash
manim-tutorial check --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --scene SceneClassName --config path/to/tutorial.toml
```

Every public TOML field is required. Set `tts.rate` to a positive playback-rate multiplier such as `1.15`; the runtime applies it without changing pitch before it derives beat and caption timing. There is no config discovery, global config, or render configuration flag. `check` does not download model weights; the first real Qwen render may download the configured model.
