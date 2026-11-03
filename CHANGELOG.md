# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- `get_constrained_packages` test kind, with `pre_packages`, `post_packages`, and `index_records` inputs, for checks on `Solver.get_constrained_packages()`
- S008 to S010, porting the three `test_packages_in_solution_change_*` tests from conda
- `names` check on `final_state`, pinning the set of package names in a solution without fixing versions or builds
- B187 to B189b, porting the record sets that conda's `tests/models/test_prefix_graph.py` builds on channel-4 and channel-5, and a `channel-5` entry in `TestChannel`

## 0.1.0 (2026-09-02)

First public release of `pytest-conda-solvers`.

### Added

- Pytest plugin that collects shared solver YAML tests and runs them against conda solver backends via `--conda-solver`
- Session-scoped mock HTTP channel server and bundled fixture channel data
- Shared solver YAML suite shipped in the wheel under `pytest_conda_solvers/conda-solver-tests/`
- `solver_tests_path()` API for locating the bundled suite, which the plugin automatically adds to pytest collection
- `--no-bundled-solver-tests` option for collecting custom tests without the bundled suite
- Packaging for PyPI with hatchling and hatch-vcs
- Support for Python 3.10 and newer

### Notes

- `conda` is not declared as a PyPI dependency; install conda (and the solver under test) via conda, mamba, or pixi before using the plugin
