# Review guidelines for pytest-conda-solver PRs

We are porting pytest tests from the original conda/conda test suite. These tests only concern the solver parts, and we are particularly interested in making sure that the solutions of the solver are consistent across different solver implementations (classic, libmamba, rattler). To do so, we have built a pytest plugin that reads inputs and outputs for a particular solver operation from YAML files. The work here is to ensure that the ported YAML test is equivalent to the original pytest test.

The `tools/update_provenance.py` script contains logic to fetch the pytest chunk from the `conda/conda` test file. Use the provenance metadata to pull the original test and compare it side by side with the ported YAML.

Raise issues like:

- Inputs do not match
- Outputs are different
- Logic is faulty

This is the list of PRs, report individually for each PR, but also compile a summary of observations that are common across PRs.

- https://github.com/conda-incubator/pytest-conda-solvers/pull/50
- https://github.com/conda-incubator/pytest-conda-solvers/pull/51
- https://github.com/conda-incubator/pytest-conda-solvers/pull/52
- https://github.com/conda-incubator/pytest-conda-solvers/pull/53
- https://github.com/conda-incubator/pytest-conda-solvers/pull/54
- https://github.com/conda-incubator/pytest-conda-solvers/pull/55
- https://github.com/conda-incubator/pytest-conda-solvers/pull/56
- https://github.com/conda-incubator/pytest-conda-solvers/pull/57


Provide proof behind all findings.

Also take a look at whether the full original test is represented in a ported YAML. For example, `test_prune_1` has two solve stages, so we expect two YAML items: `test_prune_1_1` and `test_prune_1_2`. PR #51 only includes `test_prune_1_1`.


## Jaime's Claude Session with Opus 4.6 High

https://claude.ai/share/c27fb7fa-ad85-4dc9-bb0b-ae8620ff4eef

Key findings in this table:

![image](https://hackmd.io/_uploads/SJy_E3lHze.png)


## Jannis' Codex 5.6 Sol Max

[Review of pytest-conda-solvers PRs 50 through 57](https://hackmd.io/fKHeee1ITHmknZvlaP-NUg)

### Review summary for PRs 50–57

I compared every ported YAML test against its exact upstream conda test, including all solve stages and substantive assertions.

All eight PRs need changes. The main findings are:

- Several tests port only the first stage of a multi-stage test. Examples include `test_prune_1` in PR 51, `test_priority_1` in PR 53, `test_force_reinstall_1` in PR 54, and `test_no_features` in PR 55.
- Some ports change the original inputs, including missing `add_pip`, missing timestamps, incorrect prefix handoffs, and extra repository records.
- Error tests frequently use `entries: []`, which either causes classic failures or weakens the test to “some accepted exception occurred.” Exact conflict chains, messages, and exception types are often no longer checked.
- Active libmamba branches and strict xfails are repeatedly replaced with `solvers: classic`, removing important alternate-solver coverage.
- PRs 52, 54, 55, and 56 currently have failing solver jobs. PRs 50, 51, 53, and 57 are green but still contain equivalence gaps.
- The PRs have undeclared stacking dependencies and conflicting test IDs.
- The current CI matrix covers classic and libmamba only. Rattler is not being exercised.

PR 57 is closest to complete. Its two solve stages match upstream, but the second-stage libmamba assertion is missing.

### Comparison with the Claude review

The [Claude report](https://claude.ai/share/c27fb7fa-ad85-4dc9-bb0b-ae8620ff4eef) identifies the right general risk, but its definitive findings contain several material false positives.

#### Where the reports agree

- Multi-stage tests must have every stage represented.
- PR 51 contains only the first stage of `test_prune_1`.
- `solve_final_state()` and `solve_for_diff()` must not be treated as interchangeable.
- Prefix state, environment settings, channel order, and solver-specific branches are important inputs.
- Declarative YAML cannot naturally express every assertion made through solver internals.

#### Material differences

| Finding | Claude report | Exact provenance comparison |
|---|---|---|
| `test_prune_1` | Says the source has three calls and two are missing | The pinned source has two calls. Only the second `solve_for_diff()` stage is missing. [Pinned source](https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L461-L538) |
| PR 54 B127 | Says the YAML incorrectly expects only OpenSSL instead of six packages | The pinned source expects exactly one package, OpenSSL. The YAML output is correct. [Pinned source](https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L856-L902) |
| PR 54 B129 | Says the source uses `prune=True` and expects an empty environment | The pinned source performs an ordinary solve without `prune` and restores the eight-package environment. The YAML matches it. [Pinned source](https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L903-L944) |
| `version=*` specs | Calls them deviations introduced by the YAML | The pinned source itself uses `version=*` in both relevant functions. This is not a mismatch. [Source example](https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L1013-L1034) |
| B046 | Suggests the YAML’s `UnsatisfiableError` contradicts a successful upstream solve | The pinned source explicitly expects `UnsatisfiableError` for that stage. [Pinned function](https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L1037-L1120) |
| Tests “entirely absent” | Lists `test_only_deps_2`, `test_update_all_1`, and `test_conda_downgrade` as missing | All three already exist on the PR base. [Only-deps cases](https://github.com/conda-incubator/pytest-conda-solvers/blob/60eeaf52b4716239af12b1b3ddfb3e58f2fda8ad/conda-solver-tests/basic.yaml#L1802-L1916), [update-all cases](https://github.com/conda-incubator/pytest-conda-solvers/blob/60eeaf52b4716239af12b1b3ddfb3e58f2fda8ad/conda-solver-tests/basic.yaml#L1067-L1160), [downgrade cases](https://github.com/conda-incubator/pytest-conda-solvers/blob/60eeaf52b4716239af12b1b3ddfb3e58f2fda8ad/conda-solver-tests/basic.yaml#L543-L800) |

The pattern suggests that Claude mixed an older conda source revision with the provenance commit and inspected PR diffs without consistently accounting for tests already present on the base.

#### Important findings Claude missed

Our audit additionally found:

- PR 52 cannot collect because its live head lacks the `prune` model and runner support it assumes from PR 51.
- PR 54 fails every solver job because B048 and B049 are duplicate IDs.
- PRs 55 and 56 fail classic CI because empty `ResolvePackageNotFound` entries are compared against real `bad_deps`.
- PR 53 omits three of four `test_priority_1` stages and loses the diagnostic-message assertions from B067 and B068.
- PR 55 represents only one of four `test_no_features` solves and changes its input by omitting `add_pip`.
- PR 56 omits five logical scenarios, exact conflict chains, timestamp metadata, and pip-related inputs.
- Several active libmamba branches and strict xfails are replaced with permanent classic-only exclusion.
- PRs 54, 55, and 56 introduce cross-PR ID collisions.
- Rattler is absent from the current CI matrix.

#### Recommendation

Keep Claude’s high-level observation that multi-stage tests need a completeness audit. Do not use its definitive issue table. The PR 54 critical findings and several “missing test” claims are contradicted by the exact provenance source and current base.


## Action items

- Verify completeness
- Review all attached reviews
- Add meta test to keep track of which solver tests are ported and which ones are not.
- Review protocol:
    - Human review has no blocking concerns
    - Two different LLMs agree there are no pending concerns (Opus 4.6 High, Sol Max). Use prompt at the beginning of the document.