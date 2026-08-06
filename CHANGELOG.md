# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2026-08-05)

First public release of `pytest-conda-solvers`.

### Added

- Pytest plugin that collects shared solver YAML tests and runs them against conda solver backends via `--conda-solver`
- Session-scoped mock HTTP channel server and bundled fixture channel data
- Packaging for PyPI (hatchling + hatch-vcs) with Trusted Publishing release workflow
- Support for Python 3.10 and newer

### Notes

- `conda` is not declared as a PyPI dependency; install conda (and the solver under test) via conda, mamba, or pixi before using the plugin
- The YAML corpus under `conda-solver-tests/` is not included in the wheel; obtain it from this repository (or vendor your own suite)
