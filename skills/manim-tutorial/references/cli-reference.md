# CLI reference

Use only the explicit-config commands:

```bash
manim-tutorial check --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --scene SceneClassName --config path/to/tutorial.toml
```

Every public TOML field is required. There is no config discovery, global config, or render configuration flag. `check` does not download model weights; the first real Qwen render may download the configured model.
