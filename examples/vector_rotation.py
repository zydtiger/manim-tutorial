from manim import ORIGIN, PI, RIGHT, Arrow, Create, Indicate, Rotate

from manim_tutorial import TutorialScene


class VectorRotation(TutorialScene):
    def construct(self):
        vector = Arrow(ORIGIN, 3 * RIGHT, color="#58C4DD")
        with self.beat(
            speech="Let's begin with a vector pointing to the right.",
            caption="A vector pointing right.",
        ) as beat:
            self.play(Create(vector), run_time=beat.duration)
        with self.beat(
            speech="Now rotate it by ninety degrees.",
            caption="Rotate by 90 degrees.",
        ) as beat:
            self.play(Rotate(vector, PI / 2, about_point=ORIGIN), run_time=beat.duration)
        with self.beat(
            speech="Its direction changed, but its length stayed the same.",
            caption="Rotation preserves length.",
        ) as beat:
            self.play(Indicate(vector), run_time=beat.duration)
