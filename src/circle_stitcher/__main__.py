"""Command-line interface."""

import itertools
import math
from textwrap import dedent
from typing import Generator

import click
import pyparsing as pp
import svg

MM_PER_INCH = 25.4
PX_PER_INCH = 96  # Defined by SVG

H_lit = pp.Literal("H")
OC_lit = pp.Literal("OC")
IC_lit = pp.Literal("IC")

K_lit = pp.Literal("K")
N_lit = pp.Literal("N")
M_lit = pp.Literal("M")

L_lit = pp.Literal("L")
S_lit = pp.Literal("S")
C_lit = pp.Literal("C")

integer = pp.Word(pp.nums)
integer.set_parse_action(lambda tokens: int(tokens[0]))

k_option = K_lit + pp.pyparsing_common.fnumber("k")
n_option = N_lit + integer("n")
m_option = M_lit + integer("m")

h_option = H_lit + integer("holes")
outer_circle_option = OC_lit + pp.pyparsing_common.fnumber("outer_circle")
inner_circle_option = IC_lit + pp.pyparsing_common.fnumber("inner_circle")
l_option = L_lit + pp.DelimitedList(integer)("lengths")
s_option = S_lit + integer("start_hole")
c_option = C_lit + integer("chord_count")

statement = l_option + pp.Opt(s_option) + pp.Opt(c_option)
preamble = (
    pp.Opt(h_option)
    + pp.Opt(outer_circle_option)
    + pp.Opt(k_option)
    + pp.Opt(n_option)
    + pp.Opt(m_option)
    + pp.Opt(inner_circle_option)
)

grammar = preamble + pp.DelimitedList(pp.Group(statement), delim=";")("statements")


@click.command()
@click.version_option()
@click.option("-o", "--out", required=True, type=click.File("w"))
@click.argument("commands")
def main(out: click.utils.LazyFile, commands: str) -> None:
    """Circle Stitcher."""
    # "H 16 L 10,1 S 2 C 15"
    # "L 10,1 S 2 C 15"
    # "L 10,1 S 2 C 15 ; L 3 C 20"
    # "H 16 L 10,1 S 2 C 15 ; L 3 C 20"
    # "H 42 IC 13 L 18,1"
    # Chord count limit, starting offset, two sequences
    # "H 16 L 7,1 S 2 ; L 4 C 2"
    # Three number sequence
    # "L 16,1,10"
    # Hexagon
    # "H 42 K 0.8 N 6 M 3 IC 13 L 16,3"
    # Pentagon
    # "H 35 K 0.9 N 5 M 2 IC 13 L 15,1"

    results = grammar.parse_string(commands)

    stitcher = CircleStitcher()
    stitcher.commands_text = commands

    if results.holes:
        stitcher.holes = results.holes
    if results.outer_circle:
        stitcher.circle_r = results.outer_circle * PX_PER_INCH
    if results.k:
        stitcher.k = results.k
    if results.n:
        stitcher.sides = results.n
    if results.m:
        stitcher.m = results.m
    if results.inner_circle:
        stitcher.empty_circle_r = results.inner_circle * PX_PER_INCH

    stitcher.draw()

    for state in results.statements:
        chord_count = state.chord_count if state.chord_count else 0
        start_hole = state.start_hole if state.start_hole else 0
        stitcher.draw_sequence(list(state.lengths), chord_count, start_hole)

    stitcher.render(out)


class CircleStitcher:
    """Draw stitches around a circle following a prescribed pattern."""

    def __init__(self) -> None:
        self.svg_width = 350
        self.svg_height = 350
        self.svg_scaling = 2

        self.circle_r = 70
        self.empty_circle_r = 60

        self.empty_circle_fill = "#EBE4D6"
        self.cardboard_color = "#ffffff"
        self.empty_circle_stroke = "#dddddd"

        self.hole_r = 2
        self.hole_fill = "#EBE4D6"
        self.hole_stroke = "#333333"

        self.chord_width = "1px"
        self.chord_front_color = "#2B8FF3"
        self.chord_back_color = "#F50C00"

        self.summary_text_x = 10
        self.summary_text_y = 15
        self.summary_font_size = 12

        self.commands_text_x = 10
        self.commands_text_y = self.svg_height - 5
        self.commands_text = ""

        self.hole_font_size = 8

        self.elements: list[svg.Element] = []

        self.holes = 32

        # Controls for the roundness of the needle hole pattern
        # How much the circle pushes in or out
        # 0 makes a circle so the number of sides and m don't matter
        self.k: float = 0
        # Number of sides of the shape
        self.sides: int = 1
        # Number of points on each edge
        self.m: float = 0

        self.outer_ring = 0
        self.cur_sequence = 0

    @property
    def holes(self) -> int:
        """Get number of stitch holes."""
        return self._holes

    @holes.setter
    def holes(self, holes: int) -> None:
        self._holes = holes
        self.hole_usage = [0] * holes

    @property
    def center_x(self) -> float:
        """X origin of the circle."""
        return self.svg_width / 2

    @property
    def center_y(self) -> float:
        """X origin of the circle."""
        return self.svg_height / 2

    def draw(self) -> None:
        """Render the drawing."""
        self.elements.append(
            svg.Style(
                text=dedent(f"""
                .hole {{
                    fill: {self.hole_fill};
                    stroke: {self.hole_stroke};
                    r: {self.hole_r}px;
                }}
                .index {{
                    font-size: {self.hole_font_size}px;
                    text-anchor: middle;
                }}
                .front {{
                    stroke: {self.chord_front_color};
                    stroke-width: {self.chord_width};
                }}
                .back {{
                    stroke: {self.chord_back_color};
                    stroke-width: {self.chord_width};
                }}
                .summary {{
                    font-size: {self.summary_font_size}px;
                }}
                .seq1 {{
                    fill: #099A3C
                }}
                .seq2 {{
                    fill: #8B1828
                }}
                .seq3 {{
                    fill: #515F45
                }}
            """)
            )
        )
        self.draw_background()
        self.elements.append(
            svg.Text(
                text=f"Instructions: {self.commands_text}",
                x=self.commands_text_x,
                y=self.commands_text_y,
                class_=["summary"],
            )
        )

    def render(self, out: click.utils.LazyFile) -> None:
        """Write SVG to disk."""
        doc = svg.SVG(
            width=self.svg_width * self.svg_scaling,
            height=self.svg_height * self.svg_scaling,
            viewBox=svg.ViewBoxSpec(
                min_x=0, min_y=0, width=self.svg_width, height=self.svg_width
            ),
            elements=self.elements,
        )

        out.write(str(doc))

    def draw_background(self) -> None:
        """Draw the background elements that stitches will be on top of."""
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
                r=round(self.empty_circle_r, 1),
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
                svg.Circle(cx=round(cx, 1), cy=round(cy, 1), class_=["hole"])
            )

    def draw_sequence(
        self, lengths: list[int], chord_count: int = 0, start_hole: int = 0
    ) -> None:
        """Draw stitches around the circle following the stitch pattern."""
        gen = self.create_sequence(lengths, chord_count, start_hole)
        total_length = self.draw_chords(gen)
        self.draw_summary_text(lengths, total_length)

        self.outer_ring += max(self.hole_usage)
        self.holes = self.holes  # Reset self.hole_usage

        self.create_shell()

        self.cur_sequence += 1

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

    def draw_chords(self, gen: Generator[tuple[int, int], None, None]) -> float:
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

        return total_length

    def draw_summary_text(self, lengths: list[int], total_length: float) -> None:
        """Draw summary about sequence.

        Summary includes the steps in the sequence and total length.
        """
        self.elements.append(
            svg.Text(
                text="Sequence: " + ", ".join([str(x) for x in lengths]),
                x=self.summary_text_x,
                y=self.summary_text_y,
                class_=["summary", f"seq{self.cur_sequence}"],
            )
        )
        self.summary_text_y += self.summary_font_size

        scaled_length = math.ceil(total_length / PX_PER_INCH)
        self.elements.append(
            svg.Text(
                text=f'Length: {scaled_length}"',
                x=self.summary_text_x,
                y=self.summary_text_y,
                class_=["summary", f"seq{self.cur_sequence}"],
            )
        )
        self.summary_text_y += self.summary_font_size

    def create_shell(self) -> None:
        """Create a shell to separate each sequence's index numbers."""
        r_offset = self.hole_font_size * (self.outer_ring + 1)
        r = self.circle_r + r_offset

        path: list[svg.PathData] = []
        first = True
        for hole in range(self.holes):
            x, y = self.hole_to_xy(hole, r)
            command = svg.MoveTo if first else svg.LineTo
            path.append(command(round(x, 1), round(y, 1)))
            first = False
        path.append(svg.ClosePath())
        self.elements.append(
            svg.Path(d=path, fill_opacity=0, stroke=self.empty_circle_stroke)
        )

    def stroke_chord(self, hole1: int, hole2: int, front: bool) -> svg.Line:
        """Draw a circle chord."""
        x1, y1 = self.hole_to_xy(hole1)
        x2, y2 = self.hole_to_xy(hole2)
        cls = "front" if front else "back"
        return svg.Line(
            x1=round(x1, 1),
            y1=round(y1, 1),
            x2=round(x2, 1),
            y2=round(y2, 1),
            class_=[cls],
        )

    def stroke_index(self, hole: int, count: int) -> svg.Text:
        """Draw the text next to a hole for where it is in the sequence."""
        uses = self.hole_usage[hole % self.holes]
        r_offset = self.hole_font_size * (self.outer_ring + uses + 1) + 1
        x, y = self.hole_to_xy(hole, self.circle_r + r_offset)
        # Turn the text so the bottom is toward the center
        angle = self.hole_angle(hole) + 90

        self.hole_usage[hole % self.holes] += 1
        return svg.Text(
            text=str(count),
            x=round(x, 1),
            y=round(y, 1),
            class_=["index", f"seq{self.cur_sequence}"],
            transform=[svg.Rotate(round(angle, 1), round(x, 1), round(y, 1))],
        )

    def hole_to_xy(self, index: int, r: float = 0) -> tuple[float, float]:
        """Convert hole number to x, y coordinates.

        Hole 0 is to the right and counting is clockwise.
        """
        if r == 0:
            r = self.circle_r
        rad = self.hole_angle(index) * (math.pi / 180)
        m_pi = math.pi * self.m

        dbl_sides = 2 * self.sides
        numerator = math.cos((2 * math.asin(self.k) + m_pi) / dbl_sides)
        denominator = math.cos(
            (2 * math.asin(self.k * math.cos(self.sides * rad)) + m_pi) / dbl_sides
        )
        p = numerator / denominator

        x = r * math.cos(rad) * p
        y = r * math.sin(rad) * p
        cx = self.center_x + x
        cy = self.center_y + y
        return cx, cy

    def hole_angle(self, index: int) -> float:
        """Calculate hole's angle on the circle.

        0 degrees is to the right and angles go clockwise.
        """
        return index / self.holes * 360


if __name__ == "__main__":
    main(prog_name="circle-stitcher")  # pragma: no cover
