# Repository conventions

`manim-tutorial` is a public reusable runtime and agent skill. It must never
depend on private tutorial content, private infrastructure, or machine-local
configuration.

## Architecture

- Keep public configuration limited to the exact documented TOML schema. Every
  public field is required; reject unknown fields and never discover configs.
- Keep tutorial content in normal Manim Python. Runtime plumbing, TTS setup,
  FFmpeg commands, and config paths must remain outside generated tutorials.
- Preserve the small public API: `TutorialScene` and `self.beat(...)`.
- Keep heavyweight Qwen imports lazy so configuration and CLI checks remain
  usable without downloading a model.

## Development

- Use `uv` and the `src/` package layout. Target Python 3.12 compatibility.
- Add focused tests for behavior changes. Tests must not require a model
  download, GPU, or a full Manim render unless explicitly marked integration.
- Preserve the root MIT license for source and documentation in this repository.
- This repository's publication target is public GitHub. Keep every committed
  workflow self-contained, and do not add remotes, publish, push, tag, or
  release without explicit approval for that action.

## Git

- Work from `main` for initial bootstrap. For substantial later work, use a
  sibling worktree, a task branch, and a pull request.
- Commit format is exactly `prefix: concise imperative summary`, with no scope
  and no trailing period.
- Allowed prefixes: `feat`, `fix`, `docs`, `test`, `build`, `ci`, `refactor`,
  `skill`, `chore`.
