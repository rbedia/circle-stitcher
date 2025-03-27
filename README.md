# Circle Stitcher

[![PyPI](https://img.shields.io/pypi/v/circle-stitcher.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/circle-stitcher.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/circle-stitcher)][pypi status]
[![License](https://img.shields.io/pypi/l/circle-stitcher)][license]

[![Read the documentation at https://circle-stitcher.readthedocs.io/](https://img.shields.io/readthedocs/circle-stitcher/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/rbedia/circle-stitcher/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/rbedia/circle-stitcher/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/circle-stitcher/
[read the docs]: https://circle-stitcher.readthedocs.io/
[tests]: https://github.com/rbedia/circle-stitcher/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/rbedia/circle-stitcher
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

Tool for designing circular stitched pattern templates.

- Holes are numbered to indicate which order they are stitched.
- Thread on the front is a different color than the back.
- The size of the center hole is customizable which acts a window for seeing stitches.
- Calculates length of thread needed.
- Simple language to define patterns.
- Outputs in SVG for easy printing or import into CNC software.

## Requirements

- Python 3.10

## Installation

You can install _Circle Stitcher_ via [pip] from [PyPI]:

```console
$ pip install circle-stitcher
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Circle Stitcher_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@rbedia]'s [Hypermodern Python Cookiecutter] template.

[@rbedia]: https://github.com/rbedia
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/rbedia/cookiecutter-hypermodern-python
[file an issue]: https://github.com/rbedia/circle-stitcher/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/rbedia/circle-stitcher/blob/main/LICENSE
[contributor guide]: https://github.com/rbedia/circle-stitcher/blob/main/CONTRIBUTING.md
[command-line reference]: https://circle-stitcher.readthedocs.io/en/latest/usage.html
