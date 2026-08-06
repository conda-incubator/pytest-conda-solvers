# pytest-conda-solvers

[![PyPI version](https://img.shields.io/pypi/v/pytest-conda-solvers.svg)](https://pypi.org/project/pytest-conda-solvers)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-conda-solvers.svg)](https://pypi.org/project/pytest-conda-solvers)

A [pytest](https://github.com/pytest-dev/pytest) plugin that runs shared conda solver YAML tests against classic, libmamba, or other conda solver backends.

The PyPI package ships the plugin, fixtures, and bundled mock channel data under `pytest_conda_solvers/`. The shared YAML corpus under [`conda-solver-tests/`](conda-solver-tests/) stays in this repository; point pytest at that directory (or your own YAML suite) when you run tests.

`conda-solver-tests` pytest plugin was orginally generated with [Cookiecutter] along with [@hackebrot]'s [cookiecutter-pytest-plugin] template.

## Requirements

- Python ≥ 3.10
- A working [conda](https://docs.conda.io/) (>=26.3.0) installation in the environment (install via conda, mamba, or pixi — not from PyPI)
- The solver backend under test (for example `conda-libmamba-solver`)

## Installation

```bash
conda create -n solver-test-env conda pip
conda activate pcs-dev
pip install pytest-conda-solvers
```

For local development from a checkout:

```bash
pixi install
# or: pip install -e .
```

## Usage

Pass a YAML test directory and select a solver with `--conda-solver`:

```bash
pytest --conda-solver=libmamba path/to/conda-solver-tests
pytest --conda-solver=classic path/to/conda-solver-tests
```

From this repository with pixi:

```bash
pixi run test-libmamba-solver
pixi run test-classic-solver
```

The plugin collects `.yaml` files, starts a session-scoped mock channel server, and runs each case through the selected solver backend.

## Contributing

Contributions are welcome. It is recommended to use [pixi](https://pixi.sh/) for the development environment and run the solver test tasks above before opening a pull request.

See [RELEASING.md](RELEASING.md) for how to cut a release.

## License

Distributed under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause) license.

## Issues

If you encounter problems, please [file an issue](https://github.com/conda-incubator/pytest-conda-solvers/issues).
