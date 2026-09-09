# How the YAML test harness works

This page explains how `pytest-conda-solvers` mechanically turns a `.yaml`
file into a running pytest test: collection, dispatch, and the fixtures a
test body actually runs against. See [Motivation](motivation) for *why*
the project exists, [Conda solver tests](../reference/dataset) and the
[test schema](../reference/test-schema) for the shape of a test case's
data, and [Adding a test](../how-to/adding-a-test) for the practical steps
to author one. This page assumes you've read the [Quick start](../quickstart)
but not the plugin source.

## Collection: from `.yaml` file to pytest item

Not every `.yaml` file pytest finds is treated as a solver suite. During
collection, the plugin's `pytest_collect_file` hook probes each `.yaml` file
with a cheap `msgspec.yaml.decode` and only claims it if the result is a
mapping with a top-level `tests:` list; anything else — a YAML file that
happens to live in a test directory for unrelated reasons — decodes to
something else, raises `msgspec.DecodeError`, or is simply skipped, so it's
left for other collectors.

The bundled suite under `pytest_conda_solvers/conda-solver-tests/` doesn't
need to be passed on the command line: at session start, the plugin appends
that directory to pytest's collection arguments, so it's always included
alongside whatever paths you pass explicitly. `--no-bundled-solver-tests`
turns this off, which is useful for running only your own custom YAML or
Python tests without the shipped dataset — those custom files still go
through the same `tests:`-list detection if they're `.yaml`.

Once a file is claimed, collection proceeds in three steps:

1. The whole file decodes into a `TestModule`, whose `tests` field is a list
   of test specs (see [Dispatch](#dispatch-kind-test_function-and-parametrization)
   below).
2. For each spec, the plugin loads a fresh copy of the module holding the
   base test implementations and binds it to that one entry.
3. That binding is turned into a test class named after the entry's `name`
   (spaces replaced with underscores), so each YAML entry becomes its own
   pytest class with a stable, readable node ID.

One detail worth calling out: the module in step 2 is loaded with
`importlib.util.module_from_spec` and `exec_module` rather than a normal
`import` — every test entry gets its own fresh module object instead of a
cached one. This is how the harness keeps each entry's test class
independent even though they all ultimately come from the same
`base_tests/install.py` file.

All of this decoding happens through `msgspec` models with
`forbid_unknown_fields=True`. A typo'd field name in your YAML fails
immediately at collection time with a decode error, rather than silently
being ignored — see the [test schema](../reference/test-schema) for the
exact fields each model accepts.

If you inspect `pytest --collect-only` output, you may notice that
parametrization (described next) briefly creates an unparametrized
"template" item alongside the real, parametrized one for each test method.
The plugin deselects that template item before the run, so only the
parametrized instance — the one actually bound to a YAML entry — is ever
collected or executed.

## Dispatch: `kind`, `test_function`, and parametrization

Every test entry has a `kind` discriminator, and each `kind` maps to a
default `test_function`:

| `kind` | default `test_function` |
|---|---|
| `solve` | `test_solve` |
| `solve_for_diff` | `test_solve_for_diff` |
| `determine_constricting_specs` | `test_determine_constricting_specs` |
| `unsatisfiable` | `test_unsatisfiable` |

`test_function` can be overridden per-entry, though in practice it rarely
needs to be — it exists so an entry could point at a different method than
its `kind`'s default.

The four methods named above live on a single `TestBasic` class and are each
marked `@pytest.mark.conda_solver_test`. During test generation,
`pytest_generate_tests` matches a marked method's name against the current
entry's `test_function`, and when they match, parametrizes that method's
`test` fixture with the entry itself (the decoded spec object, not just its
raw YAML). This is the mechanism that turns one YAML entry into one
concrete, runnable test: the method's `test` argument *is* the parsed test
spec.

Inside `TestBasic`, each method builds a real conda `Solver` from the
entry's `input` (via a shared `_setup_solver` context manager and
`get_solver()`), runs the corresponding solver operation, and asserts the
result against the entry's `output` or `error`. The exact fields available
on `input`/`output`/`error` are documented in the
[test schema](../reference/test-schema) rather than repeated here.

## `--conda-solver` and per-test `solvers`/`xfail_solvers`

`--conda-solver` selects which backend the whole run exercises (default
`libmamba`). The `solver_backend` fixture resolves that name to a real
backend class through conda's own plugin manager, so the harness always
solves against an actual registered backend, not a stub.

A test entry can further restrict itself to specific backends. Both checks
happen inside `pytest_generate_tests`, before the test body ever runs, and
in this order:

1. If the entry has a `solvers` allow-list and the currently selected
   `--conda-solver` isn't in it, the test is parametrized as `SKIPPED` with
   a reason naming the applicable solvers — the test body never executes.
2. Otherwise, if the selected solver is listed in `xfail_solvers`, the test
   is parametrized with a strict `xfail` (using `xfail_reason` if given, or
   a generic message otherwise) — the test body *does* run, but is expected
   to fail, and it's an error if it unexpectedly passes.
3. Otherwise, the test is parametrized normally.

## Supporting fixtures

A few fixtures do the real work behind each test method:

- `solver_backend` — resolves `--conda-solver` to a real backend class via
  conda's plugin manager, as described above.
- `env` (backed by `SimpleEnvironment`) — a helper for writing `conda-meta`
  prefix records and `repodata.json` files to a temporary directory, used by
  the classic-solver-style, filesystem-based setup path.
- `channel_server` — a session-scoped fixture that starts a real FastAPI/
  uvicorn HTTP server on a background daemon thread, serving the bundled
  `repodata.json`/`current_repodata.json` fixture data. This means a test
  entry's `channels` resolve against real HTTP URLs during a solve, not
  mocked-out Python objects. See the `TestChannel` enum in the
  [test schema](../reference/test-schema) for the list of channels it
  serves.

## Running the shipped dataset

The most direct way to run everything is plain pytest with a solver
selected — the bundled suite is collected automatically:

```bash
pytest --conda-solver=classic
pytest --conda-solver=libmamba
```

The pixi tasks `pixi run test-classic-solver` and
`pixi run test-libmamba-solver` also run the bundled suite this way, but
they point at `tests/test_provenance.py` explicitly — that file is a
separate meta-test suite that validates dataset invariants (unique names/
ids, provenance links resolving against GitHub), not part of the harness
described on this page.

To run only tests you pass explicitly, without the bundled dataset, add
`--no-bundled-solver-tests`.

See the [Quick start](../quickstart) for a first run end-to-end, and
[Adding a test](../how-to/adding-a-test) for using `-k <name>` to iterate on
a single case while authoring it.

## A non-YAML contrast case

Not every test in this project comes from a YAML file.
`base_tests/solve.py` holds a handful of "white-box" tests
(`TestSolveRegressions`) that reach into a solver's internals (the classic
solver's `SolverStateContainer`, specifically) and are written as an
ordinary pytest class in a regular `.py` file
(`conda-solver-tests/test_solve_regressions.py`). These bypass the YAML
collection machinery described above entirely; they exist because a few
upstream regressions can't be expressed as the declarative, backend-agnostic
`input`/`output` shape the rest of the dataset uses.

## See also

- [Conda solver tests](../reference/dataset) and the
  [test schema](../reference/test-schema) for the full data shape.
- [Adding a test](../how-to/adding-a-test) for authoring a new case.
- [Motivation](motivation) for why this project and its dataset exist.
