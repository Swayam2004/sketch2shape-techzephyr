"""Draw the synthetic test sketches in this folder.

    uv run python samples/test_cases/make_sketches.py

The strokes carry a small random wobble so they look drawn by hand. The seed is fixed, so two
runs give the same files. These are our own drawings, not taken from any dataset.
"""

from __future__ import annotations

import itertools
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512
WIDTH = 7
Point = tuple[float, float]


class Pen:
    def __init__(self, seed: int) -> None:
        self.img = Image.new("RGB", (SIZE, SIZE), "white")
        self.draw = ImageDraw.Draw(self.img)
        self.rng = random.Random(seed)

    def _wobble(self, p: Point) -> Point:
        return (p[0] + self.rng.uniform(-1.8, 1.8), p[1] + self.rng.uniform(-1.8, 1.8))

    def poly(self, pts: list[Point], closed: bool = False) -> None:
        if closed:
            pts = [*pts, pts[0]]
        dense: list[Point] = []
        for a, b in itertools.pairwise(pts):
            steps = max(2, int(math.dist(a, b) / 14))
            dense += [
                (a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps)
                for t in range(steps)
            ]
        dense.append(pts[-1])
        self.draw.line([self._wobble(p) for p in dense], fill="black", width=WIDTH, joint="curve")

    def arc(self, cx: float, cy: float, rx: float, ry: float, a0: float, a1: float) -> None:
        n = max(8, int(abs(a1 - a0) / 8))
        pts = [
            (
                cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)),
            )
            for i in range(n + 1)
        ]
        self.poly(pts)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float) -> None:
        self.arc(cx, cy, rx, ry, 0, 360)

    def rect(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)


def mug(p: Pen) -> None:
    p.ellipse(240, 150, 95, 28)
    p.poly([(145, 150), (155, 380)])
    p.poly([(335, 150), (325, 380)])
    p.arc(240, 380, 85, 30, 0, 180)
    p.arc(345, 250, 70, 80, -80, 80)


def table(p: Pen) -> None:
    p.poly([(60, 190), (452, 190), (452, 225), (60, 225)], closed=True)
    for x in (85, 405):
        p.poly([(x, 225), (x, 440)])
        p.poly([(x + 28, 225), (x + 28, 440)])
        p.poly([(x, 440), (x + 28, 440)])
    p.poly([(113, 255), (377, 255)])


def lamp(p: Pen) -> None:
    p.ellipse(256, 450, 85, 20)
    p.poly([(256, 430), (256, 230)])
    p.poly([(170, 230), (342, 230), (390, 90), (122, 90)], closed=True)
    p.arc(256, 90, 134, 22, 180, 360)


def house(p: Pen) -> None:
    p.rect(100, 230, 412, 440)
    p.poly([(80, 235), (256, 90), (432, 235)])
    p.poly([(340, 150), (340, 95), (385, 95), (385, 185)])
    p.rect(225, 330, 290, 440)
    for x in (130, 330):
        p.rect(x, 270, x + 65, 335)
        p.poly([(x + 32, 270), (x + 32, 335)])
        p.poly([(x, 302), (x + 65, 302)])
    p.ellipse(277, 388, 4, 4)


def bicycle(p: Pen) -> None:
    p.ellipse(130, 340, 85, 85)
    p.ellipse(382, 340, 85, 85)
    p.poly([(130, 340), (230, 340), (290, 200), (180, 200), (130, 340)])
    p.poly([(230, 340), (180, 200)])
    p.poly([(290, 200), (382, 340)])
    p.poly([(290, 200), (275, 150), (320, 140)])
    p.poly([(160, 185), (205, 185)])
    p.poly([(180, 200), (182, 185)])
    p.poly([(215, 355), (245, 355)])


def robot(p: Pen) -> None:
    p.rect(180, 80, 332, 190)
    p.poly([(256, 80), (256, 40)])
    p.ellipse(256, 32, 9, 9)
    p.ellipse(222, 130, 14, 14)
    p.ellipse(290, 130, 14, 14)
    p.poly([(226, 168), (286, 168)])
    p.rect(165, 205, 347, 355)
    p.ellipse(215, 260, 14, 14)
    p.ellipse(256, 300, 14, 14)
    p.ellipse(297, 260, 14, 14)
    p.poly([(165, 225), (105, 270), (105, 330)])
    p.poly([(347, 225), (407, 270), (407, 330)])
    p.rect(195, 355, 245, 450)
    p.rect(267, 355, 317, 450)
    p.poly([(180, 450), (255, 450)])
    p.poly([(257, 450), (332, 450)])


def sailboat(p: Pen) -> None:
    p.poly([(70, 360), (440, 360), (380, 440), (130, 440)], closed=True)
    p.poly([(250, 360), (250, 60)])
    p.poly([(262, 80), (400, 335), (262, 335)], closed=True)
    p.poly([(238, 120), (110, 335), (238, 335)], closed=True)
    p.poly([(250, 60), (300, 75), (250, 90)])
    p.arc(256, 470, 230, 12, 10, 170)


def guitar(p: Pen) -> None:
    p.ellipse(256, 385, 105, 90)
    p.ellipse(256, 290, 72, 62)
    p.ellipse(256, 340, 30, 30)
    p.poly([(238, 235), (238, 90)])
    p.poly([(274, 235), (274, 90)])
    p.poly([(225, 90), (225, 30), (287, 30), (287, 90)], closed=True)
    for x in (246, 256, 266):
        p.poly([(x, 100), (x, 440)])
    p.poly([(215, 470), (297, 470)])


CASES = {
    "mug": mug,
    "table": table,
    "lamp": lamp,
    "house": house,
    "bicycle": bicycle,
    "robot": robot,
    "sailboat": sailboat,
    "guitar": guitar,
}


def main() -> None:
    out = Path(__file__).parent
    for i, (name, fn) in enumerate(CASES.items()):
        pen = Pen(seed=100 + i)
        fn(pen)
        pen.img.save(out / f"{name}.png")


if __name__ == "__main__":
    main()
