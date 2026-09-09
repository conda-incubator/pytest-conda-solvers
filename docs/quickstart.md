# Quick start

This walks through installing `pytest-conda-solvers` and running the bundled
suite of conda solver tests against a real solver backend.

## Install

Create an environment with conda and a solver backend, then install the
plugin from PyPI:

```bash
conda create -n solver-test-env conda conda-libmamba-solver pip
conda activate solver-test-env
python -m pip install pytest-conda-solvers
```

`pytest-conda-solvers` is a pytest plugin, so installing it registers itself
automatically — there's nothing else to configure.

## Run the bundled suite

Select a solver backend with `--conda-solver`. The suite of YAML tests
shipped with the package is collected automatically:

```bash
pytest --conda-solver=classic
```

You should see a few hundred tests pass, each one a solver scenario ported
from conda's own test suite (dependency resolution, updates, pinning,
conflicts, and more). Run the same suite again against libmamba:

```bash
pytest --conda-solver=libmamba
```

Some tests are restricted to one backend or the other — those show up as
`SKIPPED` rather than failing.

## Run a single test

Every test has a human-readable name that becomes its pytest ID. Use `-k` to
run just one while you're exploring:

```bash
pytest --conda-solver=classic -k solve_1_1
```

## Look at what actually ran

`solve_1_1` above comes from a YAML file, not Python code. Here it is,
roughly:

```yaml
tests:
  - name: solve_1_1
    id: B001
    kind: solve
    input:
      channels: channel-1
      specs_to_add: numpy
    output:
      final_state:
        - channel-1/${{ arch }}::python-3.3.2-0
        - channel-1/${{ arch }}::numpy-1.7.1-py33_0
        # ...
```

The plugin reads this file, solves `numpy` against the bundled `channel-1`
fixture with whichever solver backend you selected, and asserts that the
result matches `output.final_state` exactly.

## Next steps

- Add your own test case: [Adding a test](how-to/adding-a-test)
- Look up every field a test case can have: [test schema](reference/test-schema)
- Understand what the dataset is and why it exists this way:
  [Conda solver tests](reference/dataset) and [Motivation](explanation/motivation)
- Understand how the plugin collects and runs YAML tests:
  [How the YAML test harness works](explanation/yaml-test-harness)
