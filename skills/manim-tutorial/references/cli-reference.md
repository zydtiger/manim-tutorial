# CLI reference

Use only the explicit-config commands:

```bash
manim-tutorial check --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --config path/to/tutorial.toml
manim-tutorial render path/to/tutorial.py --scene SceneClassName --config path/to/tutorial.toml
```

Every public TOML field is required. Set `tts.rate` to a positive playback-rate multiplier such as `1.15`; the runtime applies it without changing pitch before it derives beat and caption timing. There is no config discovery, global config, or render configuration flag. `check` does not download model weights; the first real Qwen render may download the configured model.

`tts.provider` selects one of two mutually exclusive `[tts]` schemas:

- `provider = "qwen3"` requires `provider`, `model`, `voice`, `language`, `device`, `rate`. It narrates with a preset speaker from a CustomVoice checkpoint.
- `provider = "qwen3-clone"` requires `provider`, `model`, `ref_audio`, `ref_text`, `language`, `device`, `rate`, and rejects `voice` as unknown. It narrates in a cloned voice from a personal reference recording, using a Base checkpoint such as `Qwen/Qwen3-TTS-12Hz-0.6B-Base` (`...-1.7B-Base` is a configuration-only quality upgrade). `ref_audio` is a path to the reference recording (a relative path resolves against the configuration file's directory) and `ref_text` is its exact transcript. `check` reports reference-audio status without loading the model.
