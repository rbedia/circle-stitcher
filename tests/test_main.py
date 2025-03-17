"""Test cases for the __main__ module."""

import os
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from circle_stitcher import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main_succeeds(runner: CliRunner, chtmpdir: Path) -> None:
    """It exits with a status code of zero."""
    out = chtmpdir / "out"
    out.mkdir()
    result = runner.invoke(__main__.main)
    assert result.exit_code == 0


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
