from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from ..config import ManimTutorialConfigError, load_config
from .check import check_environment
from .render import execute_render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manim-tutorial")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate explicit configuration and runtime prerequisites")
    check.add_argument("--config")
    render = commands.add_parser("render", help="render a tutorial with explicit configuration")
    render.add_argument("tutorial")
    render.add_argument("--scene")
    render.add_argument("--config")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if not arguments.config:
        parser.error("--config is required")
    try:
        config = load_config(Path(arguments.config), output_base=Path.cwd())
        if arguments.command == "check":
            print("Configuration")
            print(f"  ✓ {config.source_path}")
            print("\nRuntime")
            ready, lines = check_environment(config)
            print("\n".join(lines))
            if ready:
                print("\nReady.")
                return 0
            print("\nNot ready.")
            return 1
        artifacts = execute_render(arguments.tutorial, config, arguments.scene)
        print(f"Rendered: {artifacts.video}")
        if config.captions.enabled:
            print(f"Subtitles: {artifacts.subtitles}")
        if config.captions.burn:
            print(f"Captioned video: {artifacts.captioned_video}")
        print(f"Timeline: {artifacts.timeline}")
        return 0
    except ManimTutorialConfigError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
