# Conda solver tests

The solver tests are expressed in YAML files.
The formal JSON Schema can be seen [here](test-schema).
Each YAML file has a top-level `tests` entry, under which a list of individual tests follows.
Each test can take one of four possible forms, targeting four different aspects of the solver interface.
All tests share some common structure, such as general identifying information, and solver configuration like used channels and the prior state of the environment.
Additionally, each type of test has its own test information, such as the expected final solution for solver tests, or the expected error condition for unsatisfiable requests.

## Common test structure

All tests share a `name`, a unique `id`, `provenance` information linking the
test back to its upstream source, and a `kind` discriminator selecting one of
the four test types: `solve`, `solve_for_diff`, `unsatisfiable`, or
`determine_constricting_specs`. Each test also has an `input` describing the
solver inputs, such as the packages and channels involved and the prior state
of the environment.

For the full, always-up-to-date field definitions and examples for each of
these — including `input` and every test kind's specific fields — see the
[test schema](test-schema) page, which is generated directly from the
project's models and validated on every docs build.
