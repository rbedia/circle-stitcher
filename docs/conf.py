"""Sphinx configuration."""

import click
from sphinx.application import Sphinx

project = "Circle Stitcher"
author = "Rafael Bedia"
copyright = "2025, Rafael Bedia"  # noqa: A001
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"


def process_description(app: Sphinx, ctx: click.Context, lines: list[str]) -> None:  # noqa: ARG001
    """Append some text to the "example" command description."""
    for index, line in enumerate(lines):
        # Escape reStructuredText * (italics) since they aren't used
        # and having unmatched * raises a warning.
        if " *" in line:
            lines[index] = line.replace(" *", " \\*")


def setup(app: Sphinx) -> None:  # noqa: D103
    app.connect("sphinx-click-process-description", process_description)
