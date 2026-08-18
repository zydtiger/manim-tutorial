"""Public runtime API for narrated Manim tutorials."""

__version__ = "0.1.0"

__all__ = ["TutorialBeat", "TutorialScene", "__version__"]


def __getattr__(name: str):
    """Avoid importing Manim and TTS dependencies for CLI/config-only use."""
    if name == "TutorialBeat":
        from .scene.beat import TutorialBeat

        return TutorialBeat
    if name == "TutorialScene":
        from .scene.tutorial_scene import TutorialScene

        return TutorialScene
    raise AttributeError(name)
