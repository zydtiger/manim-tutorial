---
name: manim-tutorial
description: Create or revise narrated mathematical tutorials with Manim and the manim-tutorial runtime. Use when asked to explain a mathematical idea as an animated video, author a TutorialScene lesson, plan narration beats and captions, or render/review a mathematical Manim tutorial.
---

# Manim Tutorial

Build an intuitive, mathematically correct tutorial in normal Python + Manim.
Use the runtime for execution; keep the teaching decisions in the tutorial.

## Workflow

1. Establish the audience, prerequisite knowledge, and one central insight.
2. Plan conceptual beats before coding. For every beat state the speech, concise caption, visible objects, one main visual action, and why the timing helps.
3. Write a meaningful `<tutorial.py>` filename and subclass `TutorialScene`.
4. Use `with self.beat(speech=..., caption=...) as beat:` and synchronize the visual action with `run_time=beat.duration`.
5. Run `manim-tutorial check --config <config.toml>`, then render with the same explicit config. Inspect the output and revise mathematical, visual, or pacing problems before considering the tutorial complete.

Never put a config path, Qwen initialization, FFmpeg command, or output plumbing in tutorial source. Never invent a YAML animation DSL. Do not invoke Manim directly for a `TutorialScene`: the CLI supplies the required explicit runtime configuration.

## Teaching rhythm

Move through: question → show → intuition → name the idea → symbols → transform → equation/visual connection → aha → pause → recap. Show an object before its notation. Introduce one major conceptual idea at a time, and let the narration refer to what is visible now. Prefer a continuous evolving scene over repeatedly clearing the screen.

Read [references/pedagogy.md](references/pedagogy.md) when selecting the core insight or ordering an explanation; [references/lesson-rhythm.md](references/lesson-rhythm.md) when planning beats; and [references/manim-patterns.md](references/manim-patterns.md) when choosing an animation technique. Read the focused narration, caption, and visual-design references while writing those parts. Read [references/cli-reference.md](references/cli-reference.md) before running.

## Beat rules

A beat normally contains one spoken idea, one short caption, and one primary visual action. Speech may be more natural and detailed than the caption. Do not add unrelated objects, notation, and a claim in the same beat. Use a brief visual pause after an important transformation.

## Review

Check each claim, sign, axis, label, and transformation. Confirm text is readable at the chosen resolution, captions do not duplicate dense on-screen text, objects remain visually stable across transformations, and the final recap returns to the central insight. Treat render failures as diagnostics: fix missing explicit config or runtime prerequisites rather than adding hidden fallback behavior.
