"""Test cases for the __main__ module."""

import os
from pathlib import Path
from typing import Generator

import pytest
import svg
from click.testing import CliRunner

from circle_stitcher.__main__ import CircleStitcher
from circle_stitcher.__main__ import main


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main_succeeds(runner: CliRunner, chtmpdir: Path) -> None:
    """It exits with a status code of zero."""
    args = [
        "--out",
        str(chtmpdir / "test.svg"),
        "W 4 H 42 OC 2 K 0.5 N 5 M 1 IC 13 L 18,1",
    ]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0


def test_main_minimum_input(runner: CliRunner, chtmpdir: Path) -> None:
    """It exits with a status code of zero."""
    args = ["--out", str(chtmpdir / "test.svg"), "L 18,1"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0


def test_main_mm(runner: CliRunner, chtmpdir: Path) -> None:
    """It exits with a status code of zero."""
    args = ["--mm", "--out", str(chtmpdir / "test.svg"), "L 18,1"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0


def test_draw_background(stitcher: CircleStitcher) -> None:
    """Tests draw_background."""
    stitcher.draw_background()
    elements = stitcher.elements

    assert elements[0] == svg.Rect(
        x=0, y=0, width=1000, height=1000, fill=stitcher.theme.cardboard_color
    )

    assert isinstance(elements[1], svg.Circle)
    assert elements[1].cx == stitcher.center_x
    assert elements[1].cy == stitcher.center_y
    assert elements[1].r == pytest.approx(stitcher.empty_circle_r, rel=1e-1)


def test_draw_holes() -> None:
    """Tests draw_holes."""
    small = CircleStitcher()
    small.holes = 4
    small.svg_width = 1000
    small.svg_height = 1000
    small.circle_r = 100

    small.draw_holes()

    elements = small.elements
    assert len(elements) == 4
    assert isinstance(elements[0], svg.Circle)
    assert elements[0].class_ == ["hole"]
    assert elements[0].cx == pytest.approx(600.0)
    assert elements[0].cy == pytest.approx(500.0)

    assert isinstance(elements[1], svg.Circle)
    assert elements[1].class_ == ["hole"]
    assert elements[1].cx == pytest.approx(500.0)
    assert elements[1].cy == pytest.approx(600.0)

    assert isinstance(elements[2], svg.Circle)
    assert elements[2].class_ == ["hole"]
    assert elements[2].cx == pytest.approx(400.0)
    assert elements[2].cy == pytest.approx(500.0)

    assert isinstance(elements[3], svg.Circle)
    assert elements[3].class_ == ["hole"]
    assert elements[3].cx == pytest.approx(500.0)
    assert elements[3].cy == pytest.approx(400.0)


def test_create_sequence(stitcher: CircleStitcher) -> None:
    """Tests create_sequence."""
    seq = list(stitcher.create_sequence([7, 1]))
    assert seq == [(0, 7), (7, 8), (8, 15), (15, 16)]

    seq = list(stitcher.create_sequence([7, 1], chord_count=3))
    assert seq == [(0, 7), (7, 8), (8, 15)]

    seq = list(stitcher.create_sequence([7, 1], chord_count=2, start_hole=2))
    assert seq == [(2, 9), (9, 10)]


def test_draw_chords(stitcher: CircleStitcher) -> None:
    """Tests draw_chords."""
    chords = [(0, 4), (4, 8)]
    # total_length = stitcher.draw_chords(chords)
    total_length = stitcher.draw_chords(x for x in chords)
    assert total_length == pytest.approx(282.8427)

    elements = stitcher.elements
    assert len(elements) == 5
    assert elements[0].text == "1"
    assert isinstance(elements[1], svg.Line)
    assert elements[1].class_ == ["front"]
    assert elements[2].text == "2"
    assert isinstance(elements[3], svg.Line)
    assert elements[3].class_ == ["back"]
    assert elements[4].text == "3"


def test_draw_summary_text(stitcher: CircleStitcher) -> None:
    """Tests draw_summary_text."""
    stitcher.draw_summary_text([10, 1], 1000.5)

    seq = stitcher.elements[-2]
    assert isinstance(seq, svg.Text)
    assert seq.text == "Sequence: 10, 1"
    assert seq.x == 10
    assert seq.y == 15
    assert seq.class_ == ["summary", "seq0"]

    length = stitcher.elements[-1]
    assert isinstance(length, svg.Text)
    assert length.text == 'Length: 11"'
    assert length.x == 10
    assert length.y == 27
    assert length.class_ == ["summary", "seq0"]

    assert stitcher.summary_text_y == 39


def test_stroke_chord(stitcher: CircleStitcher) -> None:
    """Tests stroke_chord."""
    line = stitcher.stroke_chord(0, 8, front=True)
    assert line.class_ == ["front"]
    assert line.x1 == pytest.approx(600.0)
    assert line.y1 == pytest.approx(500.0)
    assert line.x2 == pytest.approx(400.0)
    assert line.y2 == pytest.approx(500.0)

    line = stitcher.stroke_chord(4, 12, front=False)
    assert line.class_ == ["back"]
    assert line.x1 == pytest.approx(500.0)
    assert line.y1 == pytest.approx(600.0)
    assert line.x2 == pytest.approx(500.0)
    assert line.y2 == pytest.approx(400.0)


def test_stroke_index(stitcher: CircleStitcher) -> None:
    """Tests stroke_index."""
    text = stitcher.stroke_index(2, 1)
    assert text.text == "1"
    assert text.x == pytest.approx(577.1)
    assert text.y == pytest.approx(577.1)
    assert text.transform
    assert len(text.transform) == 1
    assert isinstance(text.transform[0], svg.Rotate)
    assert text.transform[0].a == pytest.approx(135.0)

    # Second label at the same hole is offset further from the center
    text = stitcher.stroke_index(2, 2)
    assert text.text == "2"
    assert text.x == pytest.approx(582.7)
    assert text.y == pytest.approx(582.7)
    assert text.transform
    assert len(text.transform) == 1
    assert isinstance(text.transform[0], svg.Rotate)
    assert text.transform[0].a == pytest.approx(135.0)


def test_hole_to_xy(stitcher: CircleStitcher) -> None:
    """Tests hole_to_xy."""
    assert stitcher.hole_to_xy(0) == pytest.approx((600.0, 500.0))
    assert stitcher.hole_to_xy(2) == pytest.approx((570.7106, 570.7106))
    assert stitcher.hole_to_xy(4) == pytest.approx((500.0, 600.0))
    assert stitcher.hole_to_xy(8) == pytest.approx((400.0, 500.0))
    assert stitcher.hole_to_xy(12) == pytest.approx((500.0, 400.0))

    assert stitcher.hole_to_xy(0, r=200) == pytest.approx((700.0, 500.0))
    assert stitcher.hole_to_xy(2, r=200) == pytest.approx((641.4213, 641.4213))


def test_hole_angle(stitcher: CircleStitcher) -> None:
    """Tests hole_angle."""
    assert stitcher.hole_angle(0) == 0.0
    assert stitcher.hole_angle(1) == 1 / 16 * 360
    assert stitcher.hole_angle(8) == 180
    assert stitcher.hole_angle(15) == 15 / 16 * 360
    assert stitcher.hole_angle(16) == 360.0
    assert stitcher.hole_angle(17) == 17 / 16 * 360


@pytest.fixture
def stitcher() -> CircleStitcher:
    """Basic CircleStitcher fixture."""
    stitch = CircleStitcher()
    stitch.holes = 16
    stitch.svg_width = 1000
    stitch.svg_height = 1000
    stitch.circle_r = 100
    return stitch


@pytest.fixture
def chtmpdir(tmpdir: Path) -> Generator[Path, None, None]:
    """Change current working directory to tmpdir."""
    yield from _chdir(tmpdir)


def _chdir(dstdir: Path) -> Generator[Path, None, None]:
    """Change current working directory to dstdir."""
    lwd = Path.cwd()
    os.chdir(dstdir)
    try:
        yield dstdir
    finally:
        os.chdir(lwd)
