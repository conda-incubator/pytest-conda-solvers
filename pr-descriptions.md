# Updated PR descriptions

Full replacement bodies for PRs 50 to 57: the original description with the audit-and-fix
changes woven in at the end. Copy each block wholesale into the PR.

## PR 50, [01] Rework splits of tests, add descriptions for constricting_specs and CUDA tests

This is part of a stack of PRs that I have derived from #38, having ported the tests from #1. I'm splitting #38 into smaller PRs. My aim is not entirely to create a stack in the literal sense, but to make it easier and reduce the churn associated with merge conflicts for the tests (though I might make the case to put a series of related PRs on a stack for later PRs).

This first PR:
- adds descriptions for the constricting_specs-based tests and CUDA tests
- moves the `test_freeze_deps` tests from the basic YAML tests into the integration YAML tests (to reflect conda upstream, though there's not much of a difference here).
- updates the provenance and IDs for some tests

Following a full fidelity audit of the ported suite against upstream at the pinned commit, this PR also carries the resulting harness corrections. The runner previously compared solved states as unordered sets and never enforced the declared exception type, both of which are now fixed, and a new must-solve mode covers tests where upstream only asserts that the solve succeeds. The audit's fixes for the tests introduced here are included too, notably per-solver CUDA error-message variants (C003b, C004b), the previously unported first invocation of `test_pinned_1` (I000), and the libmamba branch of `test_conda_downgrade` stage 4 (B179).

## PR 51, [02] Add an assortment of various core solve and dependency tests

This PR is derived from #38 and is the second part of the stack. It is recommended to review #50 before this, as there will be some merge conflicts and it will be easier to resolve them after that one is merged. I've added the `prune` tests here that I was previously trying to add in #17, and also an assortment of various tests from `tests/core/test_solve.py`:
- `test_timestamps_1`
- `test_solve_2_1`
- `test_prune_1_1`
- `test_remove_with_constrained_dependencies_1`, `test_indirect_dep_optimized_by_version_over_package_count_1`, and
- `test_indirect_dep_optimized_by_version_over_package_count_2`.

The fidelity-audit follow-up lands here as well. It corrects solver-order expectations now that the harness enforces order, converts B113 to a strict libmamba xfail to match upstream's mark, and tweaks the white-box ssc regression test so duplicate records cannot collapse in its order assertion.

## PR 52, [03] Add tests of the update/auto-update/update-prune family

This PR is part of a series of PRs derived from #38. My recommendation is to review #50 and #51 first, as #51 adds the `prune` step for the test harness. The changes here:
- the fast-update tests (`test_fast_update_with_update_modifier_not_set`)
- the update-prune tests (`test_update_prune_1_1`). Not that there is any duplication, because some tests rely on the same baseline but differ afterwards in subsequent tests. I chose to keep this duplication so that things are easier to understand later on.

The audit fixes for this PR's tests are included as well. The update-prune smoke stages that upstream never asserts on now use the harness's must-solve mode (the B145 per-solver split collapses back into one entry), the xfail mapping for B117 and B147 mirrors upstream's marks, and the fast-update diff test gains the per-solver expectations upstream actually branches on.

## PR 53, [04] Add downgrade, pinning, and priority tests

This PR is derived from #38. I recommend reviewing the earlier PRs in the series (#50, #51, and #52) first.

Here, we port scenarios around downgrades of conda and Python, pinned packages, and channel priority. They verify that the solvers honour pins and channel priority when a requested change would otherwise raise a conflict.

The audit fixes are included too. The downgrade-prevention error tests now assert upstream's message snippets, with new libmamba variants (B067b, B068b) where the wording differs, and the channel-priority scenarios carry corrected expectations under the order-enforcing harness. A few descriptions now disclose where upstream's own assertions were never enforced because of non-strict xfails there.

## PR 54, [05] Add force-reinstall, unfreeze-when-required, and force-remove tests

This is yet another PR derived from #38. I would recommend reviewing the first four PRs in the series first: #50, #51, #52, and #53

I've ported the unfreeze-when-required, force-reinstall, and force-remove scenarios, and added the small channel-freeze fixture they use. These tests cover cases where the solver must either break or deliberately preserve an existing environment.

The audit fixes here are mostly re-orderings of pinned states into true solver order now that the harness enforces it, plus an a/b split of the force-remove stage where the two solvers link the same records in different orders (B128, B128b).

## PR 55, [06] Add tests for features and track-features

This PR is derived from #38 and is one among a series of PRs that includes #50, #51, #52, #53, and #54.

This PR ports the classic-only feature scenarios: mkl and track-features installs, surplus features, install-with-feature, and glob match-spec compatibility. I have split the cases in which the classic and libmamba solvers diverge.
- I've added the small channels 7, 8, 9, and 10 fixtures, plus one extra record in channel 1.
- Some are marked classic-only because libmamba does not model features the same way.

The audit fixes are included as well. The globstr-compatible smoke stages become must-solve entries (their per-solver splits collapse back into B135 and B136, likewise B139), the feature tests upstream skips for libmamba are now restricted accordingly, and the remaining pinned states are re-ordered for the order-enforcing harness. The white-box globstr test's docstring now references all four ported case ids.

## PR 56, [07] Add some synthetic solver-scenario tests

Yet another PR derived from #38. This is in a series of PRs that comprises #50, #51, #52, #53, #54, and #55 – please review them first.

This PR ports the `SolverTests` scenarios with an assortment of purpose-made tests, such as reduced-index broadening, the shortest-chain and some other unsatisfiable cases, arch-versus-noarch preference, and timestamp tie-breaks. I've added a consolidated channel-7 fixture that holds all of these prefixed package families.

The audit fixes are included here too. The unsatisfiable scenarios now assert upstream's actual conflict chains instead of empty entries, with libmamba message variants where the wording differs (B062b, B063b, B064b), and the nonexistent-package tests solve against a new empty channel fixture to match upstream's empty repodata. Order expectations and a couple of provenance stage numbers are corrected as well.

## PR 57, [08] Add integration tests for Python2-update scenarios

This is, yet again, derived from #38. I think this should be the last PR in this series – if you're reading this, thank you for getting here! The previous PRs in the series are #50, #51, #52, #53, #54, #55, and #56. This PR adds the Python 2 update scenarios to the integration test suite. This PR can be reviewed independently, but it does build on the integration fixtures that were reworked earlier in the stack.

One audit fix is included here: the pinned 31-record libmamba state in I017b is re-ordered from alphabetical to the true solver order, which the harness now enforces.
