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

- Use `uv` and the `src/` package layout. Support Python 3.11 through 3.13;
  keep Python 3.12 as the default local development version.
- Add focused tests for behavior changes. Tests must not require a model
  download, GPU, or a full Manim render unless explicitly marked integration.
- Preserve the root MIT license for source and documentation in this repository.
- This repository's publication target is public GitHub. Keep every committed
  workflow self-contained, and do not add remotes, publish, push, tag, or
  release without explicit approval for that action.
- Commit hooks are defined in `.pre-commit-config.yaml` and run with `prek`.
  Install the runner once with `uv tool install prek`, then activate the hooks
  in this checkout with `prek install`.

## Git

- Work from `main` for initial bootstrap. For substantial later work, use a
  sibling worktree, a task branch, and a pull request.
- Commit format is exactly `prefix: concise imperative summary`, with no scope
  and no trailing period.
- Allowed prefixes: `feat`, `fix`, `docs`, `test`, `build`, `ci`, `refactor`,
  `skill`, `chore`.

## Versioning and releases

- Follow Semantic Versioning. Before 1.0, use PATCH for backward-compatible
  fixes and MINOR for new capabilities or any intentional breaking change.
  Starting at 1.0, use MAJOR for breaking public API, CLI, or configuration
  changes, MINOR for backward-compatible features, and PATCH for fixes.
- Keep the version identical in `pyproject.toml`,
  `src/manim_tutorial/__init__.py`, and `uv.lock`. Use a focused
  `build: bump version to X.Y.Z` commit for a release candidate.
- Publish releases only through GitHub Releases in this repository. Never
  publish this project to PyPI or another package index. Changing the release
  destination requires an explicit user-approved policy change first.
- Prepare release notes from commits since the previous `vX.Y.Z` tag and state
  compatibility or migration requirements. Validate the locked environment,
  tests, source distribution, wheel metadata, and an isolated wheel install.
- Before every release, present the exact version, target commit, destination,
  release notes, and validation evidence to the user. Require explicit approval
  for that exact candidate before creating or pushing a tag or creating a
  GitHub Release.
- Treat each version as a new approval gate. Approval does not carry to another
  version or destination, and any change to the target commit, artifacts, or
  release notes invalidates the prior approval.
