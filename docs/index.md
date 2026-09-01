# pytest-conda-solvers

This repository contains two things: a set of tests for conda ecosystem solvers expressed
as declarative YAML files, and a pytest plugin that can run those tests against any solver
registered via the standard conda plugin system.

:::{warning}
This project is still in early stages of development. Don't use it in production (yet).
We do welcome feedback on what the expected behaviour should have been if something doesn't work!
:::
:::{grid-item-card} Getting started
Once `pytest-conda-solvers` is installed in an environment with conda and the solver backend under test, run the bundled suite with:

:::
::::


```{toctree}
:hidden:
conda-solver-tests
test-schema
```
