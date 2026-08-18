# Manim patterns

Use `MathTex` only after the represented object is visible. Use `TransformMatchingTex` when algebra evolves so matching structure persists. Use `ValueTracker` with `always_redraw` for a continuously changing quantity. Use `Axes` and graphs for relationships, and group/layout objects before they animate. Prefer camera movement only when it clarifies scale or focus. Keep updaters scoped and remove them when their role ends.
