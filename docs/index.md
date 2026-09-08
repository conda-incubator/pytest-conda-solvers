# pytest-conda-solvers

A [pytest](https://github.com/pytest-dev/pytest) plugin that runs shared
conda solver YAML tests against classic, libmamba, or other conda solver
backends.

The PyPI package ships the plugin, fixtures, mock channel data, and shared
YAML suite under `pytest_conda_solvers/`. When the plugin loads, it
automatically adds the bundled suite to pytest's collection.

:::{warning}
This project is still in early stages of development. Don't use it in production (yet).
We do welcome feedback on what the expected behaviour should have been if something doesn't work!
:::

## Requirements

- Python ≥ 3.10
- A working [conda](https://docs.conda.io/) (>=26.3.0) installation in the environment (install via conda, mamba, or pixi — not from PyPI)
- The solver backend under test (for example `conda-libmamba-solver`)

## Installation

```bash
conda create -n solver-test-env conda conda-libmamba-solver pip
conda activate solver-test-env
python -m pip install pytest-conda-solvers
```

For local development from a checkout:

```bash
pixi install
# or: pip install -e .
```

## Usage

Select a solver with `--conda-solver`; the bundled suite is collected automatically:

```bash
pytest --conda-solver=libmamba
pytest --conda-solver=classic
```

Paths passed to pytest are collected alongside the bundled suite, so solver
authors can add their own Python or YAML tests normally.

Use `--no-bundled-solver-tests` to collect custom tests without the suite
shipped by this package.

From this repository with pixi:

```bash
pixi run test-libmamba-solver
pixi run test-classic-solver
```

The plugin collects solver-suite `.yaml` files, starts a session-scoped mock
channel server, and runs each case through the selected solver backend. See
the [Quick start](quickstart) tutorial for a walkthrough.

## Contributing

Contributions are welcome. It is recommended to use [pixi](https://pixi.sh/)
for the development environment and run the solver test tasks above before
opening a pull request. See [Adding a test](how-to/adding-a-test) to
contribute a new solver test case.

Build the documentation locally with `pixi run -e docs docs-build`.

## License

Distributed under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause) license.

## Issues

If you encounter problems, please [file an issue](https://github.com/conda-incubator/pytest-conda-solvers/issues).

---

::::{grid} 2
:gutter: 3

:::{grid-item-card} {octicon}`rocket` Quick start
:link: quickstart
:link-type: doc

Install the plugin and run the bundled solver test suite in a few minutes.
:::

:::{grid-item-card} {octicon}`tools` How-to guides
:link: how-to/index
:link-type: doc

Task-oriented guides for extending the suite, such as adding a new test.
:::

:::{grid-item-card} {octicon}`book` Reference
:link: reference/dataset
:link-type: doc

The dataset's structure and the full JSON Schema for every test field.
:::

:::{grid-item-card} {octicon}`light-bulb` Explanation
:link: explanation/motivation
:link-type: doc

Background on why this project exists and how it strengthens error checks.
:::

::::

```{toctree}
:hidden:
:caption: Tutorials

quickstart
```

```{toctree}
:hidden:
:caption: How-to guides

how-to/index
how-to/adding-a-test
```

```{toctree}
:hidden:
:caption: Reference

reference/dataset
reference/test-schema
```

```{toctree}
:hidden:
:caption: Explanation

explanation/motivation
explanation/error-assertion-semantics
```
