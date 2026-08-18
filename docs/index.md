# pytest-conda-solvers

This repository contains two things: a set of tests for conda ecosystem solvers expressed
as declarative YAML files, and a pytest plugin that can run those tests against any solver
registered via the standard conda plugin system.

:::{warning}
This project is still in early stages of development. Don't use it in production (yet).
We do welcome feedback on what the expected behaviour should have been if something doesn't work!
:::

::::{grid} 1

:::{grid-item-card} Getting started
The easiest way to get started is using pixi.
To run all the tests against the classic solver, just run

```
pixi run test-classic-solver
```
:::
::::


```{toctree}
:hidden:
conda-solver-tests
test-schema
```
