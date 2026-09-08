# Motivation

## Why a shared solver test suite?

conda supports multiple solver backends — the original "classic" solver and
libmamba are both bundled with conda today, and the plugin system that
selects between them is open to other implementations (e.g.
[conda-rattler-solver](https://github.com/conda/conda-rattler-solver)). Each
backend can legitimately make different tradeoffs internally, but from a user's
perspective a given set of channels, installed packages, and requested specs
should still resolve the same way (or fail the same way) regardless of which
backend is running.

To not overburden the existing conda test suite by adding more
test scenarios each time we add a solver backend, this project was created
to organize the most important test cases crucial to determining
correct solver behavior. This central repository determining correct behavior
for a solver can then be used in each individual solver backend's testing
suite.

## Why YAML instead of Python?

Each test case in this project's dataset is a declarative YAML document: a
`kind` (a full solve, a solve-for-diff, a constricting-specs check, or an
expected failure), an `input` (channels, specs, prior prefix state, solver
flags), and an expected `output` or `error`. None of it is Python code that
depends on conda's internal test helpers.

That matters for two reasons:

- **Portability.** The pytest plugin that ships with this project is only
  one possible runner. Because a case is just data, any harness — including
  a solver plugin's own CI — can load it and run it against a backend
  registered through conda's plugin system, using `--conda-solver` to pick
  which one.
- **Auditability.** A YAML case is easy to read, diff, and review without
  understanding conda's test infrastructure. Reviewers can compare a case
  directly against the upstream test it came from.

## Why track provenance?

Almost every case in the dataset was ported from an existing test in
[conda/conda](https://github.com/conda/conda), and each one records exactly
where: the pytest node ID, the commit it was ported from, and a permalink to
the source, validated in CI against the real file at that commit (see
[Adding a test](../how-to/adding-a-test)). This isn't just bookkeeping:

- It keeps the dataset honest. A case that can't be traced back to a real
  upstream test and line range fails CI, so the dataset can't silently drift
  into asserting behavior nobody has actually reasoned about.
- It makes the porting itself auditable — a reviewer can open the exact
  upstream lines a case claims to represent and check the translation.
- It lets tooling (`tools/collect_ported_node_ids.py`) turn the dataset back
  into a list of upstream pytest node IDs, so the ported YAML cases can be
  run side by side with conda's *own* suite as a fidelity check, and
  (`tools/update_provenance.py`) keep that link current as conda's source
  evolves.

## What this project is not

`pytest-conda-solvers` doesn't implement a solver, and it isn't trying to
replace or duplicate conda's own test suite. It's a compatibility and
regression suite that sits alongside conda: a shared set of ported scenarios
that any solver backend can be measured against, plus the pytest plugin that
runs them.
