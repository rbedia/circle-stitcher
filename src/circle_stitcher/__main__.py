"""Command-line interface."""

import itertools
import math
from pathlib import Path
from typing import Generator

import click
import pyparsing as pp
import svg

MM_PER_INCH = 25.4

H_lit = pp.Literal("H")
IC_lit = pp.Literal("IC")
L_lit = pp.Literal("L")
S_lit = pp.Literal("S")
C_lit = pp.Literal("C")

integer = pp.Word(pp.nums)
integer.set_parse_action(lambda tokens: int(tokens[0]))

h_option = H_lit + integer("holes")
inner_circle_option = IC_lit + integer("inner_circle")
l_option = L_lit + pp.DelimitedList(integer)("lengths")
s_option = S_lit + integer("start_hole")
c_option = C_lit + integer("chord_count")

statement = l_option + pp.Opt(s_option) + pp.Opt(c_option)
grammar = (
    pp.Opt(h_option)
    + pp.Opt(inner_circle_option)
    + pp.DelimitedList(pp.Group(statement), delim=";")("statements")
)


@click.command()
@click.version_option()
@click.argument("commands")
def main(commands: str) -> None:
    """Circle Stitcher."""
    # "H 16 L 10,1 S 2 C 15"
    # "L 10,1 S 2 C 15"
    # "L 10,1 S 2 C 15 ; L 3 C 20"
    # "H 16 L 10,1 S 2 C 15 ; L 3 C 20"

    results = grammar.parse_string(commands)
    holes = 32
    if results.holes:
        holes = results.holes
    inner_circle_r = 15.875
    if results.inner_circle:
        inner_circle_r = results.inner_circle
    stitcher = CircleStitcher(holes, inner_circle_r)
    stitcher.draw()

    for state in results.statements:
        chord_count = state.chord_count if state.chord_count else 0
        start_hole = state.start_hole if state.start_hole else 0
        stitcher.draw_sequence(state.lengths, chord_count, start_hole)

    stitcher.render()


class CircleStitcher:
    """Draw stitches around a circle following a prescribed pattern."""

    def __init__(self, holes: int, empty_circle_r: int) -> None:
        self.svg_width = 840
        self.svg_height = 1000

        self.scaling = 300 / 20.434

        self.circle_r = 300
        self.empty_circle_r = empty_circle_r * self.scaling

        self.empty_circle_fill = "#eeeecc"
        self.cardboard_color = "#ffffff"
        self.empty_circle_stroke = "#dddddd"

        self.hole_r = 10
        self.hole_fill = "#fbfbc5"
        self.hole_stroke = "#333333"

        self.chord_front_color = "#ff0000"
        self.chord_back_color = "#33cc33"

        self.summary_text_x = 10
        self.summary_text_y = 30
        self.summary_font_size = 30

        self.hole_font_size = 18

        self.center_x = self.svg_width / 2
        self.center_y = self.svg_height / 2

        self.elements: list[svg.Element] = []

        self.holes = holes

        self.hole_usage = [0] * self.holes

    def draw(self) -> None:
        """Render the drawing."""
        self.draw_background()

        # self.draw_sequence([2, 2])
        # self.draw_sequence([10, 1])
        # self.draw_sequence([12, 11])
        # self.draw_sequence([15, 11])
        # self.draw_sequence([1, 13])

        # self.draw_sequence([15, 1])
        # self.draw_sequence([15, 1], start_hole=1)
        # self.draw_sequence([16, 1])
        # self.draw_sequence([16, 1, 14, 4])

        # self.draw_sequence([13, 3])
        # self.draw_sequence([13, 3], start_hole=2)

        # self.draw_sequence([13, 3, 6, 1, 2])
        # self.draw_sequence([1, 9, 2, 9])
        # self.draw_sequence([1, 11, 2, 11])
        # self.draw_sequence([1, 10, 2, 11])

        # self.draw_sequence([10, 2, 19, 3])

        # self.draw_sequence([10, 2, 19, 3, 15, 1])
        # self.draw_sequence([10, 2, 19, 3, 13, 3])
        # self.draw_sequence([10, 2, 19, 3, 16, 1])

        # self.draw_sequence([12, 14])
        # self.draw_sequence([12, 14], start_hole=1)
        # self.draw_sequence([19, 17], start_hole=3)

        # self.draw_sequence([3, 12, 5, 13], chord_count=100)
        # self.draw_sequence([14, 1, 8, 1])

    def render(self) -> None:
        """Write SVG to disk."""
        doc = svg.SVG(
            width=self.svg_width,
            height=self.svg_height,
            elements=self.elements,
        )

        filename = "out/circle.svg"
        Path(filename).write_text(str(doc))

    def draw_background(self) -> None:
        """Draw the background elements that stitches will be on top of."""
        # Fill entire canvas with a solid color to draw on top of
        self.elements.append(
            svg.Rect(
                x=0,
                y=0,
                width=self.svg_width,
                height=self.svg_height,
                fill=self.cardboard_color,
            )
        )

        # Large center hole
        self.elements.append(
            svg.Circle(
                cx=self.center_x,
                cy=self.center_y,
                r=self.empty_circle_r,
                fill=self.empty_circle_fill,
                stroke=self.empty_circle_stroke,
            )
        )

        self.draw_holes()

    def draw_holes(self) -> None:
        """Draw perimeter needle holes."""
        for i in range(self.holes):
            cx, cy = self.hole_to_xy(i)
            self.elements.append(
                svg.Circle(
                    cx=cx,
                    cy=cy,
                    r=self.hole_r,
                    fill=self.hole_fill,
                    stroke=self.hole_stroke,
                )
            )

    def draw_sequence(
        self, lengths: list[int], chord_count: int = 0, start_hole: int = 0
    ) -> None:
        """Draw stitches around the circle following the stitch pattern."""
        gen = self.create_sequence(lengths, chord_count, start_hole)
        self.draw_sequence_from_gen(gen, lengths)

    def create_sequence(
        self, lengths: list[int], chord_count: int = 0, start_hole: int = 0
    ) -> Generator[tuple[int, int], None, None]:
        """Generate stitches around the circle following the stitch pattern."""
        index = start_hole
        first = True

        len_cycle = itertools.cycle(lengths)

        for _ in range(chord_count if chord_count else 10000):
            increment = next(len_cycle)
            if (
                not chord_count > 0
                and not first
                and increment == lengths[0]
                and index == start_hole
            ):
                break
            end_index = index + increment
            yield index, end_index

            index = end_index % self.holes
            first = False

    def draw_sequence_from_gen(
        self, gen: Generator[tuple[int, int], None, None], lengths: list[int]
    ) -> None:
        """Draw stitches around the circle following the stitch pattern."""
        front = True
        first = True

        count = 1
        total_length = 0.0

        for index, end_index in gen:
            if first:
                self.elements.append(self.stroke_index(index, count))
                count += 1

            self.elements.append(self.stroke_chord(index, end_index, front))
            self.elements.append(self.stroke_index(end_index, count))

            x1, y1 = self.hole_to_xy(index)
            x2, y2 = self.hole_to_xy(end_index)

            total_length += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            front = not front
            count += 1
            first = False

        self.elements.append(
            svg.Text(
                text="Sequence: " + ", ".join([str(x) for x in lengths]),
                x=self.summary_text_x,
                y=self.summary_text_y,
                font_size=self.summary_font_size,
            )
        )
        scaled_length = total_length / self.scaling / MM_PER_INCH
        self.elements.append(
            svg.Text(
                text=f'Length: {scaled_length:0.1f}"',
                x=self.summary_text_x,
                y=self.summary_text_y + self.summary_font_size,
                font_size=self.summary_font_size,
            )
        )

    def stroke_chord(self, hole1: int, hole2: int, front: bool) -> svg.Line:
        """Draw a circle chord."""
        x1, y1 = self.hole_to_xy(hole1)
        x2, y2 = self.hole_to_xy(hole2)
        stroke_color = self.chord_front_color if front else self.chord_back_color
        return svg.Line(x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke_color, stroke_width=3)

    def stroke_index(self, hole: int, count: int) -> svg.Text:
        """Draw the text next to a hole for where it is in the sequence."""
        uses = self.hole_usage[hole % self.holes]
        r_offset = self.hole_font_size * (uses + 1)
        x, y = self.hole_to_xy(hole, self.circle_r + r_offset)
        # Turn the text so the bottom is toward the center
        angle = self.hole_angle(hole) + 90

        self.hole_usage[hole % self.holes] += 1
        return svg.Text(
            text=str(count),
            x=x,
            y=y,
            font_size=self.hole_font_size,
            text_anchor="middle",
            transform=[svg.Rotate(angle, x, y)],
        )

    def hole_to_xy(self, index: int, r: float = 0) -> tuple[float, float]:
        """Convert hole number to x, y coordinates.

        Hole 0 is to the right and counting is clockwise.
        """
        if r == 0:
            r = self.circle_r
        k = 0.5
        n = 7
        m = 5
        rad = self.hole_angle(index) * (math.pi / 180)
        p = math.cos((2 * math.asin(k) + math.pi * m) / (2 * n)) / math.cos(
            (2 * math.asin(k * math.cos(n * rad)) + math.pi * m) / (2 * n)
        )
        # inscribed
        # p = math.cos(math.pi / n) /
        # math.cos(rad - (2 * math.pi / n *
        # math.floor((n * rad + math.pi) / (2 * math.pi))))

        # circumscribed
        # p = 1 / math.cos((2 / n) * math.asin(math.sin((n / 2) * rad)))

        x = r * math.cos(rad) * p
        y = r * math.sin(rad) * p
        cx = self.center_x + x
        cy = self.center_y + y
        return cx, cy

    # def hole_to_xy(self, index: int, r: float = 0) -> tuple[float, float]:
    #     """Convert hole number to x, y coordinates.

    #     Hole 0 is to the right and counting is clockwise.
    #     """
    #     if r == 0:
    #         r = self.circle_r
    #     rad = self.hole_angle(index) * (math.pi / 180)
    #     x = math.cos(rad) * r
    #     y = math.sin(rad) * r
    #     cx = self.center_x + x
    #     cy = self.center_y + y
    #     return cx, cy

    def hole_angle(self, index: int) -> float:
        """Calculate hole's angle on the circle.

        0 degrees is to the right and angles go clockwise.
        """
        return index / self.holes * 360


if __name__ == "__main__":
    main(prog_name="circle-stitcher")  # pragma: no cover
