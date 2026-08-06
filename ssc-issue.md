# The SolverStateContainer problem in `test_solve_2`

All links are pinned to conda commit `03329e0f4a627c9b9aa92ef34f7f93b9aa83e438`, the provenance commit our YAML tests use.

## The issue in short

The final stage of `test_solve_2` bypasses the solver's public API. It reaches into classic's internal `SolverStateContainer` (`solver.ssc`), injects a duplicate `mkl` record into `solution_precs`, sets `add_back_map`, and mocks the private `_run_sat` method to return that doctored state, asserting that the add-back logic deduplicates the final state by package name. Because it mutates solver internals and mocks a private method (and libmamba has no `ssc` at all, which is why upstream skips it there), it cannot be expressed as a declarative YAML input/output spec. We ported it verbatim as a classic-only white-box test in `pytest_conda_solvers/base_tests/solve.py` instead.

## The relevant test

- Whole test: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L127-L203
- The exact offending lines (ssc mutation, `_run_sat` mock, dedup assert): https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L185-L203
- Construction of the injected duplicate record: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L161-L183
- The libmamba skip naming `Solver.ssc` as the reason: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L128-L131

## The product code being exercised

- `SolverStateContainer` class: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/core/solve.py#L1324-L1400
- Where `Solver` creates and stores it as `self.ssc`: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/core/solve.py#L333-L342
- The add-back handling the test exercises: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/core/solve.py#L415-L419 and https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/core/solve.py#L1089-L1090 (inside `_run_sat`, which starts at https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/core/solve.py#L977)
