# Adding a test to the dataset

This page walks through porting one upstream conda solver test into the YAML
dataset in `pytest_conda_solvers/conda-solver-tests/`. See
[Conda solver tests](../reference/dataset) for what the dataset is, and the
[test schema](../reference/test-schema) for the full field reference — this page is a
practical, step-by-step companion to that reference.

:::{note}
Every test case must trace back to a real test in the
[conda/conda](https://github.com/conda/conda) repository via its `provenance`
block (see [Provenance](#provenance) below). There's currently no supported
way to add a case that isn't anchored to an existing upstream conda test
function — if you want to exercise a scenario upstream doesn't already cover,
find the closest related upstream test and cite it, explaining the deviation
in `description` (see [strengthening a check](#strengthening-a-check)).
:::

## 1. Find the upstream test

Pick a test from conda's own suite — typically
`tests/core/test_solve.py`, `conda/testing/solver_helpers.py`, or
`tests/test_solvers.py` at the commit currently pinned across the dataset
(check `provenance.commit` in an existing entry, e.g. `basic.yaml`). Note:

- Its exact pytest node ID (e.g.
  `tests/core/test_solve.py::test_solve_1`, or, for a class-based test,
  `conda/testing/solver_helpers.py::SolverTests.test_iopro_mkl`).
- If the upstream test performs several solves in one function body (common
  in `test_solve.py`), you'll split it into one YAML entry per solve, with a
  `::N` suffix appended to the node ID for each stage (`::1`, `::2`, ...).

## 2. Choose the kind and expected outcome

Pick the `kind` that matches what the upstream test actually asserts:

| `kind` | Use when upstream asserts... |
|---|---|
| `solve` | the full final environment state after a solve |
| `solve_for_diff` | only the packages unlinked/linked, not the whole state |
| `determine_constricting_specs` | which installed packages block an install/upgrade |
| `unsatisfiable` | the solver raises an error |

For `unsatisfiable`, also pick the `error` type
(`UnsatisfiableError`, `ResolvePackageNotFound`, `PackagesNotFoundError`, or
`SpecsConfigurationConflictError`) matching the exception upstream expects —
see the "Errors" section of the [test schema](../reference/test-schema) for the shape of
each. Classic and
libmamba sometimes raise *different* exceptions or messages for the same
scenario; when that happens, add two entries with the same node ID, restrict
each with `solvers: classic` / `solvers: libmamba`, and give the second a
`b`-suffixed id (see [Choosing an id](#choosing-an-id-and-a-file)) and a
name suffixed with `_libmamba` (e.g. `test_nonexistent_1` / id `B056`, and
`test_nonexistent_1_libmamba` / id `B056b`, in `basic.yaml`).

## 3. Pick channels, or extend the fixtures

Most tests reuse one of the bundled channels
(`channel-1` … `channel-14`, `channel-freeze`, `channel-empty`,
`conda_format_repo`) — see the `TestChannel` enumeration in the
[test schema](../reference/test-schema) for the full list, and browse
`pytest_conda_solvers/conda-solver-tests/*.yaml` for tests already using the
packages you need. Prefer an existing channel before adding a new one.

If the upstream test relies on packages that genuinely aren't covered by any
bundled channel, its repodata needs to be converted and added to
`pytest_conda_solvers/data/`. This is a heavier, code-level change (not just
a new YAML file):

1. Add `<channel-name>_noarch.json` and/or `<channel-name>_non-noarch.json`
   under `pytest_conda_solvers/data/`, derived from upstream's
   `index.json`/`repodata.json` fixtures — see the `jq` recipe at the top of
   `pytest_conda_solvers/data/__init__.py` for the expected split.
2. Add the new channel name to the `TestChannel` enum in
   `pytest_conda_solvers/models.py`.
3. If a new platform subdir is involved, also check `TestSubdir` and
   `SUBDIR_MAP` in `pytest_conda_solvers/data/__init__.py`.

Consider raising this as a separate PR/discussion first, since new fixture
data affects every test that might reuse it.

## 4. Fill in the required fields

Every test spec needs:

- **`name`** — a human-readable, globally unique name (checked by
  `tests/test_provenance.py::TestProvenanceUniqueness`). Match the upstream
  function name where practical, adding a numeric or solver-name suffix for
  split/variant stages (`solve_1_1`, `solve_1_2`, `test_nonexistent_1_libmamba`).
- **`id`** — a stable, globally unique short ID (also uniqueness-checked).
  See [Choosing an id](#choosing-an-id-and-a-file).
- **`provenance`** — see below.
- **`input`** — see [Encode inputs and outputs](#5-encode-inputs-and-outputs).
- **`output`** (or **`error`** for `unsatisfiable`).

Optional but encouraged: a `description` explaining anything not obvious
from the YAML alone — flaky upstream markers, deliberate strengthenings of
upstream's assertions, or why a particular solver is skipped/xfailed. Link to
the exact upstream lines when useful.

### Provenance

```yaml
provenance:
  node_id: tests/core/test_solve.py::test_solve_1::1
  commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
  url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L58-L124
```

- `commit` is the full 40-character SHA of the conda/conda commit the test
  was ported from — normally the same commit already pinned by other tests
  in the dataset.
- `url` must be a GitHub blob permalink at that same commit, with an
  `#L<start>-L<end>` range that matches the *exact* start/end lines of the
  test function, as parsed by AST. `tests/test_provenance.py` enforces all
  of this over the network (commit-in-URL, path-matches-node-id, valid line
  range, and that the file exists and the range matches the function
  boundary at that commit) — get this wrong and CI will fail, not just a
  local lint. The easiest way to get an exact match: open the file on GitHub
  at that commit, select the function's lines, and use GitHub's "Copy
  permalink" action.
- If you split one upstream function into multiple YAML entries, reuse the
  same `node_id`/`commit`/`url` for each, appending `::1`, `::2`, ... to
  `node_id` per stage (this suffix is stripped again by tooling like
  `tools/collect_ported_node_ids.py`).

If the dataset's pinned commit is ever bumped, `tools/update_provenance.py`
re-derives `commit`/`url` (and line ranges) for every existing entry in bulk
by AST-diffing the old and new commits — you shouldn't need it when adding a
single new test, only when the *whole dataset* moves to a newer conda
revision.

### Choosing an id and a file

Each bundled YAML file uses its own id prefix:

| File | Prefix | Covers |
|---|---|---|
| `basic.yaml` | `B` | Core solve/install scenarios |
| `integration.yaml` | `I` | Broader multi-step / integration scenarios |
| `cuda.yaml` | `C` | CUDA/glibc virtual-package overrides |
| `constricting_specs.yaml` | `S` | `determine_constricting_specs` cases |

Add your test to the file matching its `kind`/topic, using the next unused
number for that prefix (check the highest existing id in the file). Use a
trailing letter suffix (`B056b`) for a solver-specific variant of the same
upstream test, as described above. Only start a new file if you're adding a
new topical grouping that doesn't fit any existing one — pick a new,
unused prefix letter if so, and register it in this table.

## 5. Encode inputs and outputs

`input` mirrors the fields of `TestInput` (see the "Input" section of the
[test schema](../reference/test-schema) for the complete list) — most fields are optional
and can be omitted. A minimal `solve` input usually only needs `channels` and
`specs_to_add`:

```yaml
input:
  channels: channel-1
  specs_to_add: numpy
```

`history_specs` takes MatchSpec strings such as `numpy=1.7.1`.
`solution_records` takes `PrefixRecord` mappings, as documented in the
[Input section of the test schema](../reference/test-schema).

Distribution strings (used in `prefix`, `output.final_state`,
`output.unlink_precs`, and `output.link_precs`) follow the form:

```
<channel>/${{ arch }}::<name>-<version>-<build>
```

Always use the literal `${{ arch }}` placeholder rather than hardcoding
`linux-64` — the harness substitutes the actual test arch at run time. For
example:

```yaml
output:
  final_state:
    - channel-1/${{ arch }}::python-3.3.2-0
    - channel-1/${{ arch }}::numpy-1.7.1-py33_0
```

For `unsatisfiable` tests, `error.entries` takes match-spec strings (or
lists of them for multi-hop conflict chains) rather than dist strings — see
the "Errors" examples in the [test schema](../reference/test-schema) for each exception
type.

## 6. A minimal annotated example

Here's `B001` from `basic.yaml` — the first stage of a two-stage upstream
test — with every field annotated. It's a real entry already in the
dataset, not a template to copy verbatim; use it as a reference for the
shape and pick your own `name`/`id`/`provenance` as described above.

```yaml
tests:
  - name: solve_1_1          # human-readable, globally unique
    id: B001                 # short, globally unique id (next free number for the file's prefix)
    provenance:
      node_id: tests/core/test_solve.py::test_solve_1::1   # ::1 = first stage of a multi-solve upstream test
      commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438      # pinned conda/conda commit
      url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L58-L124
    kind: solve               # asserts a full final environment state
    description: |
      Optional context: why this test exists, any deliberate strengthening
      of upstream's (weaker) assertions, or solver quirks worth flagging.
    input:
      channels: channel-1      # one of the bundled TestChannel values
      specs_to_add: numpy      # string or list of match-spec strings
    output:
      final_state:              # exact, ordered expected solve result
        - channel-1/${{ arch }}::openssl-1.0.1c-0
        - channel-1/${{ arch }}::readline-6.2-0
        - channel-1/${{ arch }}::sqlite-3.7.13-0
        - channel-1/${{ arch }}::system-5.8-1
        - channel-1/${{ arch }}::tk-8.5.13-0
        - channel-1/${{ arch }}::zlib-1.2.7-0
        - channel-1/${{ arch }}::python-3.3.2-0
        - channel-1/${{ arch }}::numpy-1.7.1-py33_0
```

## 7. Validate and run locally

The plugin decodes every YAML file with `msgspec` as part of normal test
collection (`forbid_unknown_fields=True` on every model, so a typo'd field
name fails immediately with a decode error) — there's no separate schema
step to run for a plain new test case. From a repository checkout with
[pixi](https://pixi.sh/):

```bash
# run everything (bundled suite + the provenance meta-tests), per solver:
pixi run test-classic-solver
pixi run test-libmamba-solver

# or target just your new test by its `name` while iterating (spaces become
# underscores in the parametrized test id, e.g. -k solve_1_1 for "solve_1_1"):
pixi run pytest --conda-solver=classic -k "<your test's name>"
pixi run pytest --conda-solver=libmamba -k "<your test's name>"
```

Run against **both** solvers before opening a PR, unless you've deliberately
restricted the test with `solvers:` to just one of them.

If you changed `pytest_conda_solvers/models.py` (new fields, not just a new
test case), also regenerate the committed schema:

```bash
pixi run generate-schema   # or: pixi run check-schema, to only verify it's up to date
```

## 8. PR expectations

- `name` and `id` are unique across the whole dataset (`test_provenance.py`
  checks this for you locally and in CI).
- `provenance` resolves correctly against GitHub at the exact pinned commit
  (network-checked in CI).
- The test passes against classic and/or libmamba, matching whatever
  `solvers`/`xfail_solvers` you declared.
- If your change touches `pytest_conda_solvers/models.py`, the committed
  `docs/cst_schema.json` is regenerated (`pixi run check-schema` is run in
  CI and will fail on a stale schema).
- If you're bumping the dataset's pinned conda commit (as opposed to adding
  one test), that's a separate, larger change driven by
  `tools/update_provenance.py` — call it out explicitly and expect it to
  touch many existing entries, not just yours.

### Strengthening a check

It's common and encouraged to assert *more* than the upstream test does —
for example, pinning the full ordered `final_state` where upstream only
checks package count or membership. When you do this, say so explicitly in
`description`, with a link to the weaker upstream assertion, so reviewers
and future maintainers can tell an intentional strengthening apart from an
overly strict, hand-copied assumption. Several existing entries in
`basic.yaml` and `constricting_specs.yaml` follow this pattern, and
`unsatisfiable` tests strengthen error-message checks across solvers by
convention — see [Error assertion semantics](../explanation/error-assertion-semantics).
