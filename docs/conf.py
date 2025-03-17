"""Sphinx configuration."""

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
