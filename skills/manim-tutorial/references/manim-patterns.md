# Manim patterns

Use `MathTex` only after the represented object is visible. Use `TransformMatchingTex` when algebra evolves so matching structure persists. Use `ValueTracker` with `always_redraw` for a continuously changing quantity. Use `Axes` and graphs for relationships, and group/layout objects before they animate. Prefer camera movement only when it clarifies scale or focus. Keep updaters scoped and remove them when their role ends.

Keep transitions swift and display their resolved state for comprehension. For example:

```python
with self.beat(speech=speech, caption=caption) as beat:
    self.play(
        Transform(source, target),
        FadeIn(formula),
        run_time=min(1.0, beat.duration),
    )
```

The beat context automatically waits for unfinished narration after the animation. Avoid `run_time=beat.duration` unless continuous movement throughout the narration is intentionally explanatory.
