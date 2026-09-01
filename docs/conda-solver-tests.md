# Conda solver tests

Conda solver tests are written as YAML files. See the
[JSON Schema for Conda Solver Tests](test-schema) for complete field definitions
and examples.

Each file contains a top-level `tests` key with a list of test cases. Each test
case covers one of four solver operations. All test cases include identifying
information and solver input, such as channels and the initial prefix state.
Each test type adds its own expected result, such as a final solution or an
error.

## Common test structure

All tests share a `name`, a unique `id`, `provenance` information linking the
test back to its upstream source, and a `kind` discriminator selecting one of
the four test types: `solve`, `solve_for_diff`, `unsatisfiable`, or
`determine_constricting_specs`. Each test also has an `input` describing the
solver inputs, such as the packages and channels involved and the prior state
of the environment.

For complete field definitions and examples, see the [test schema](test-schema).
The JSON Schema is generated from the project models, and CI checks the
committed schema before building the documentation.
