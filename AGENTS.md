# Repository conventions

`manim-tutorial` is a private-targeted reusable runtime and agent skill. It must
never depend on content from `manim-tutorial-projects` or on machine-local
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
- Do not add a LICENSE file unless explicitly requested.
- This repository's eventual target is private. Do not add remotes, publish,
  push, or expose private infrastructure without explicit approval.

## Git

- Work from `main` for initial bootstrap. For substantial later work, use a
  sibling worktree, a task branch, and a pull request.
- Commit format is exactly `prefix: concise imperative summary`, with no scope
  and no trailing period.
- Allowed prefixes: `feat`, `fix`, `docs`, `test`, `build`, `refactor`,
  `skill`, `chore`.
