from manim_tutorial.scene.beat import TutorialBeat


def test_beat_exposes_narration_duration():
    beat = TutorialBeat(duration=2.75)
    assert beat.duration == 2.75
