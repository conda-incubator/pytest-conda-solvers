# Porting fidelity audit, 2026-08-06

A full re-audit of every ported test against its upstream original, done independently of the earlier
reviews. Sixteen auditor agents, each with a fresh context, compared all 217 ported tests one by one
against the upstream conda source at each test's pinned provenance commit (read from the local conda
clone at 26.7.0). Every comparison was done by reading both sides in full, not by any programmatic
diff. Coverage: 217 of 217 tests checked (180 in basic.yaml, 20 in integration.yaml, 7 in cuda.yaml,
7 in constricting_specs.yaml, and 3 white-box tests in base_tests/solve.py), none unverifiable.

Result: 135 findings in total, of which 8 are classed broken, 72 minor, and 55 notes. The whole suite
is currently green on CI, so almost all of these are latent fidelity gaps (the port asserts more,
less, or something different from upstream) rather than failing tests. Severity meanings: broken
means the port asserts something upstream does not or drops upstream behaviour, minor means a real
deviation unlikely to flip pass or fail, and note means cosmetic (descriptions, permalinks,
redundant fields).

Read the three harness findings first. They cut across nearly every test and change how much the
per-test findings matter.

## Harness findings (cross-cutting)

### H1: the order assertion has never enforced order

`install.py` compares `convert_to_dist_str(...)` (a boltons `IndexedSet`) against the reference from
`add_base_url` (a plain `list`). boltons `IndexedSet.__eq__` falls back to `set(self) == set(other)`
for non-IndexedSet operands, so the "exact order" asserts at install.py lines 292, 318, and 320 are
unordered content checks. Verified empirically: `IndexedSet(['x','y','z']) == ['z','y','x']` is True.
Upstream asserts exact tuple order for every expected state, so every final_state, unlink, and link
expectation in all four YAML files is currently weaker than upstream. Six auditors found this
independently.

Consequences beyond the comparison itself: several YAML lists turn out to be alphabetised rather
than in true solver order (B032, B133, and B134 below), which has been invisible because order was
never checked. Fixing the comparison (wrap both sides in `list(...)`) will surface those.

### H2: the declared exception type is never enforced for unsatisfiable tests

`test_unsatisfiable` wraps the solve in a `pytest.raises` over the union of all four mapped
exception types and then dispatches on whichever type actually arrived. The YAML `exception:` field
is looked up but never asserted against, so a test declaring `UnsatisfiableError` passes if the
solver raises `PackagesNotFoundError` instead, and any test with `entries: []` and no message fields
checks nothing beyond "some solver exception was raised". Upstream pins the exact exception class in
every `pytest.raises`. This is the known strictness gap: the spiked isinstance assert produced zero
mismatches on both solvers, so landing it closes this for every affected test at once. Affected
entries flagged individually below: B005 through B007b, B046, B052, B053, B058 through B065, B083
through B084b, B088, B105, B105b, B143, I013, and C003.

### H3: the harness asserts more than upstream for libmamba errors

For libmamba, upstream's `assert_unsatisfiable` only checks that the exception is an
`UnsatisfiableError` subclass, because the entries comparison is gated on the type being exactly
`UnsatisfiableError`. The ported runner additionally asserts that the endpoint package names of
every expected conflict chain appear in the libmamba error message, and `message_includes` adds
further content checks upstream never makes. This is a deliberate strengthening, but it is a
deviation from upstream parity and worth an explicit decision. Flagged on B005, B054b, and B153.

## Broken ports

Three patterns. First, missing solver restrictions: B003 and B095 run and assert on libmamba where
upstream explicitly skips those tests for libmamba (B094 under minor findings is the same pattern).
They pass today by luck of the channel data, not by upstream warrant. Second, invented assertions:
B135a/b, B136a/b, and B139 pin exact full states where upstream only requires that the solve does
not raise (this is the parked B135/B136 design question, and the audit adds B139 to it). Third,
B071 applies classic-only expectations to both solvers.

### B003

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_iopro_mkl`

The port runs unrestricted on both solvers, but at the pinned commit upstream explicitly skips test_iopro_mkl for libmamba because features are unsupported. The port therefore asserts a full 12-record featured solution on libmamba that upstream never asserts, and it omits the solvers or xfail_solvers restriction that sibling feature-test ports carry.

Evidence: Upstream tests/test_solvers.py at 03329e0f, lines 15-39: class TestLibMambaSolver(SolverTests) with tests_to_skip returning {"conda-libmamba-solver does not support features": ["test_iopro_mkl", ...]}. Ported basic.yaml lines 56-83 (B003) has no solvers or xfail_solvers field, so pytest_generate_tests applies no skip for --conda-solver=libmamba. Compare sibling entries B114 (line 2535) and B116 (line 2676) which set xfail_solvers: libmamba with reason "Features not supported in libmamba".

### B095

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_pseudo_boolean::1`

The port runs this stage unrestricted on both solvers, but upstream explicitly skips the whole of test_pseudo_boolean for the libmamba solver. The entry is missing a solvers: classic restriction, which the port applies to every other test in the same upstream skip list, including the sibling stage B171 (test_pseudo_boolean_2). Nothing in the description accounts for widening the test to libmamba.

Evidence: Upstream tests/test_solvers.py at commit 03329e0f: TestLibMambaSolver.tests_to_skip returns '"conda-libmamba-solver does not support features": [..., "test_pseudo_boolean", ...]'. Ported basic.yaml lines 5521-5551 (B095) have no solvers: field, while B171 (test_pseudo_boolean_2, node_id SolverTests::test_pseudo_boolean::2) declares solvers: classic, as do B130, B131, B137, B138, B140, B154-B158, B166-B170. The stage's index also contains numpy-1.5.1-py27_p4 (features: mkl) at the same build number as the expected numpy-1.5.1-py27_4, the feature tie-break upstream says libmamba does not support.

### B071

Upstream: `tests/core/test_solve.py::test_fast_update_with_update_modifier_not_set::3`

The port runs on both solvers with no solvers restriction and asserts the full classic unlink and link order, but upstream makes that assertion only in the classic branch. For libmamba, upstream deliberately weakens the checks and documents that mamba picks a different sqlite version, so the port asserts under libmamba something upstream does not, and no libmamba companion entry exists (unlike stage 2, which has B178 test_fast_update_2b).

Evidence: Upstream at 03329e0, tests/core/test_solve.py L2324-2339: 'if context.solver == "libmamba": # LIBMAMBA ADJUSTMENT # We only check sqlite was upgraded as expected and python stays the same ... # mamba chooses a different sqlite version (3.23 instead of 3.24) assert VersionOrder(sqlite.version) > VersionOrder("3.21") ... else: assert convert_to_dist_str(unlink_precs) == unlink_order'. The ported entry (basic.yaml L2307-2349) has no 'solvers:' or 'xfail_solvers:' key and its output pins 'channel-4/${{ arch }}::sqlite-3.24.0-h84994c4_0' and 'channel-4/${{ arch }}::python-2.7.15-h1571d57_0' as exact ordered expectations for both solvers. A grep of basic.yaml shows test_fast_update_2b exists (L2931) but no test_fast_update_3b.

### B135a

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::1`

The port asserts an exact 13-record final state that upstream never checks. Upstream's first stage is a pure smoke test: it only requires that solve_final_state() does not raise, with no output assertion at all, so any legitimately different solver solution would fail the port while upstream stays green.

Evidence: Upstream at 03329e0, test_solve.py L3823-L3825: 'specs = (MatchSpec("accelerate=*=np17*"), MatchSpec("accelerate=*=*np17*"))' then 'solver.solve_final_state()' with no assert and the comment 'This should work -- build strings are compatible' (L3822). Port basic.yaml L4452-L4466 pins output.final_state to 13 records including 'accelerate-1.1.0-np17py33_p0' and 'mkl-11.0-np17py33_p1'.

### B135b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::1`

Same invented assertion as B135a for the libmamba variant: upstream asserts nothing about the solution on any solver, yet the port pins a libmamba-specific 13-record final state, an expectation with no upstream basis.

Evidence: Upstream test_solve.py L3823-L3825 contains no output assertion and no solver-specific branch. Port basic.yaml L4479 'solvers: libmamba' and L4485-L4499 pin an exact final state differing from the classic variant only in 'numpy-1.7.1-py33_0' and 'scipy-0.12.0-np17py33_0'.

### B136a

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::2`

The port asserts an exact 22-record final state that upstream never checks. Upstream's second stage only requires that solve_final_state() does not raise.

Evidence: Upstream test_solve.py L3827-L3829: 'specs = (MatchSpec("accelerate=*=np17*"), MatchSpec("accelerate=*=np17py27*"))' then 'solver.solve_final_state()' with no assert. Port basic.yaml L4518-L4541 pins 22 records including 'accelerate-1.1.0-np17py27_p0' and 'numbapro-0.11.0-np17py27_p0'.

### B136b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::2`

Same invented assertion as B136a for the libmamba variant: the port pins a libmamba-specific 22-record final state where upstream asserts nothing beyond successful solving on either solver.

Evidence: Upstream test_solve.py L3827-L3829 has no output assertion. Port basic.yaml L4554 'solvers: libmamba' and L4560-L4583 pin an exact state, differing from the classic variant in mkl, numexpr, numpy, scikit-learn, and scipy builds.

### B139

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_install_package_with_feature`

The port asserts an exact 11-record final state that upstream never checks. Upstream's test only requires that the install does not raise, as its own comment states.

Evidence: Upstream at 03329e0, solver_helpers.py L802-L803: '# should not raise' followed by 'env.install("mypackage", "feature 1.0")' with no assertion on the result. Port basic.yaml L4647-L4659 pins 11 records, from 'channel-1/${{ arch }}::distribute-0.6.36-py33_1' through 'channel-10/${{ arch }}::mypackage-1.0-0'.

## Minor findings

Real deviations from upstream, unlikely to flip pass or fail today. Ordered by test id.

### B002

Upstream: `tests/core/test_solve.py::test_solve_1::2`

Upstream marks test_solve_1 flaky with reruns=5 precisely because libmamba sometimes solves this python=2 stage to python-2.6.8-6 and numpy-1.7.1-py26_0. The port asserts python-2.7.5-0 and numpy-1.7.1-py27_0 strictly, runs on libmamba, and carries no rerun, xfail, or restriction accommodation, so the intermittent libmamba outcome upstream tolerates would fail the port outright.

Evidence: Upstream test_solve.py lines 56-57: @pytest.mark.benchmark and @pytest.mark.flaky(reruns=5), with the docstring at lines 59-82 showing the observed libmamba divergence ('channel-1/linux-64::python-2.6.8-6', 'channel-1/linux-64::numpy-1.7.1-py26_0'). Ported basic.yaml B002 lines 45-54 pins python-2.7.5-0 and numpy-1.7.1-py27_0 with no xfail_solvers or solvers field, and the repo has no flaky or rerun machinery (no matches for flaky/reruns in pytest_conda_solvers or pyproject.toml).

### B004

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_anaconda_nomkl`

Upstream asserts only the record count (107) and membership of one scipy record, but the port pins the entire 107-record solution with exact versions and builds, asserting far more than upstream. Any alternative valid solution upstream would accept fails the port, and the description field does not explain the expansion.

Evidence: Upstream solver_helpers.py lines 310-314: records = env.install("anaconda 1.5.0", "python 2.7*", "numpy 1.7*"), assert len(records) == 107, assert "test::scipy-0.12.0-np17py27_0" in records. Ported basic.yaml lines 98-206 list all 107 records exactly. I verified the YAML list equals anaconda-1.5.0-np17py27_0 plus its 106 pinned depends from channel-1_non-noarch.json and includes scipy-0.12.0-np17py27_0 (line 187), so it is internally consistent, but it remains a much stronger assertion than upstream's.

### B005

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1 (equally ::2, ported as B006)`

For libmamba, upstream checks nothing beyond the exception being an UnsatisfiableError subclass, but the harness additionally asserts that the endpoint package names of every expected conflict chain appear in the libmamba error message. This is an added assertion upstream does not make and it applies identically to B006.

Evidence: Upstream solver_helpers.py lines 227-238: assert_unsatisfiable does assert issubclass(exc_info.type, UnsatisfiableError) and compares entries only 'if exc_info.type is UnsatisfiableError', which is false for LibMambaUnsatisfiableError. Port install.py lines 377-390: in the libmamba branch (unsatisfiable is None) it collects entry_tuple[0].name and entry_tuple[-1].name for each expected chain and asserts 'name in message' for each, so B005 requires numpy and scipy, and B006 requires numpy and python, in the libmamba message.

### B019

Upstream: `tests/core/test_solve.py::test_conda_downgrade::1`

The port runs unrestricted and strict on libmamba, but upstream applies a non-strict xfail to the whole of test_conda_downgrade when the solver is libmamba because it is known flaky. The port drops that allowance, so a flaky libmamba failure that upstream tolerates becomes a hard failure. Assertion content itself matches upstream exactly.

Evidence: Upstream test_solve.py lines 1315-1324 at commit 03329e0f: 'if context.solver == "libmamba": request.applymarker(pytest.mark.xfail(context.solver == "libmamba", reason="Known flaky:https://github.com/conda/conda-libmamba-solver/issues/317"))'. basic.yaml entry B019 (lines 569-625) has no solvers or xfail_solvers field and no description.

### B020

Upstream: `tests/core/test_solve.py::test_conda_downgrade::2`

Same as B019: the port runs strict on libmamba where upstream carries a non-strict known-flaky xfail on libmamba for the whole test, and the port has no xfail_solvers or description accounting for it.

Evidence: Upstream test_solve.py lines 1318-1324 (xfail on libmamba, reason 'Known flaky'). basic.yaml B020 (lines 627-688) has no solvers, xfail_solvers, or description fields.

### B021

Upstream: `tests/core/test_solve.py::test_conda_downgrade::3`

Same as B019 and B020: strict libmamba run in the port versus upstream's non-strict known-flaky xfail on libmamba covering this stage.

Evidence: Upstream test_solve.py lines 1318-1324 (xfail on libmamba). basic.yaml B021 (lines 690-753) has no solvers, xfail_solvers, or description fields.

### B022

Upstream: `tests/core/test_solve.py::test_conda_downgrade::4 (libmamba branch)`

The port restricts stage 4 to classic and drops upstream's libmamba branch, which runs the same solve and checks conda < 4.4.10, python == 3.6.2, conda-build == 3.12.1, and itsdangerous == 0.24 on the link records. Upstream does not skip libmamba here (it only carries the non-strict flaky xfail), and no description on the entry says the libmamba case is ported elsewhere. The classic branch itself is ported faithfully, including exact unlink and link lists and order.

Evidence: Upstream test_solve.py lines 1508-1524 at commit 03329e0f: 'if context.solver == "libmamba": ... for pkg in link_precs: if pkg.name == "conda": assert VersionOrder(pkg.version) < VersionOrder("4.4.10") elif pkg.name == "python": assert pkg.version == "3.6.2" ...'. basic.yaml B022 line 762 'solvers: classic' with no description field anywhere in the entry (lines 755-887).

### B023

Upstream: `tests/core/test_solve.py::test_channel_priority_churn_minimized::1`

The port asserts a full 43-record final_state for stage 1, but upstream performs no assertion at all on this solve: it only computes final_state and pprints it. The pinned list was synthesised to enable the chained B024a and B024b prefixes (it matches them exactly), but it is enforced on both solvers, so any solver producing a different valid solution fails the port while passing upstream.

Evidence: Upstream test_solve.py lines 2778-2781 at commit 03329e0f: 'with get_solver_aggregate_2(tmpdir, specs) as solver: final_state = solver.solve_final_state()' followed only by 'pprint(convert_to_dist_str(final_state))', with no order tuple and no assert for this stage. basic.yaml B023 output.final_state lines 905-947 lists 43 channel-4 records asserted by the solve runner.

### B024a

Upstream: `tests/core/test_solve.py::test_channel_priority_churn_minimized::2 (classic branch)`

Upstream asserts only the lengths of the diff, one unlinked and one linked record, for both solvers. The port asserts exact identities (unlink channel-4 itsdangerous-0.24-py37_1, link channel-2/noarch itsdangerous-0.24-py_0). The pinned identities match the docstring's stated intent for the churn-minimised reinstall, but they are stronger than anything upstream enforces, so a different single-package diff would fail the port while passing upstream.

Evidence: Upstream test_solve.py lines 2802-2803 at commit 03329e0f: 'assert len(unlink_dists) == 1' and 'assert len(link_dists) == 1' are the only assertions for this stage. basic.yaml B024a output lines 1012-1015 pins 'channel-4/${{ arch }}::itsdangerous-0.24-py37_1' and 'channel-2/noarch::itsdangerous-0.24-py_0'.

### B024b

Upstream: `tests/core/test_solve.py::test_channel_priority_churn_minimized::2 (libmamba branch)`

Same strengthening as B024a: upstream asserts only len == 1 for unlink and link on libmamba, while the port pins the exact outcome (unlink and relink of the same channel-4 itsdangerous-0.24-py37_1 build). The description's claim that libmamba reinstalls the same build rather than switching to the channel-2 noarch build is an empirical observation not present in upstream, which never checks which records are involved. The force_reinstall: true input does faithfully mirror upstream's libmamba-only solver_kwargs, and the description's first claim matches upstream's comment about the solver considering the state satisfying.

Evidence: Upstream test_solve.py lines 2783-2788 ('With libmamba v2, we need this extra flag ... the solver considers the current state as satisfying', solver_kwargs = {"force_reinstall": True}) and lines 2802-2803 (length-only asserts). basic.yaml B024b lines 1087-1091 pins unlink and link both to 'channel-4/${{ arch }}::itsdangerous-0.24-py37_1', and the description lines 1025-1031 states the switch-versus-reinstall behaviour.

### B032

Upstream: `tests/core/test_solve.py::test_update_deps_1::5`

The ported expected final_state order deviates from the order upstream asserts. Upstream places unixodbc-2.3.1-0 first in the stage-5 expectation, while the port places it sixth, in the alphabetical slot it occupies in the stage-4 expectation. The record set is identical, only the order differs, so the port asserts an ordering that contradicts the upstream assertion.

Evidence: Upstream at commit 03329e0f, tests/core/test_solve.py lines 2146-2158: the order tuple begins 'channel-1::unixodbc-2.3.1-0', then 'channel-1::openssl-1.0.1c-0', 'channel-1::readline-6.2-0', and so on. Ported basic.yaml lines 1364-1374: final_state begins with openssl, readline, sqlite, system, tk, and only then 'channel-1/${{ arch }}::unixodbc-2.3.1-0' at line 1370, before zlib. All ten records match, positions 0 to 5 do not.

### B046

Upstream: `tests/core/test_solve.py::test_only_deps_2::3`

The harness's unsatisfiable runner does not enforce the declared exception class. Upstream requires UnsatisfiableError specifically, but the port's pytest.raises accepts any of UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, or SpecsConfigurationConflictError, and with entries empty the match arms make no further check. A solver raising PackagesNotFoundError or ResolvePackageNotFound here would pass the ported test but fail upstream.

Evidence: Upstream line 1089: 'with pytest.raises(UnsatisfiableError):' around the stage-3 solve_final_state. pytest_conda_solvers/base_tests/install.py test_unsatisfiable lines 356-363 use 'pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError))', and nothing afterwards asserts isinstance(exc_info.value, error_info["exception"]). Ported basic.yaml lines 2066-2068 declare 'exception: UnsatisfiableError' with 'entries: []', so every entry check is skipped.

### B052

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1`

Upstream's classic-solver unsatisfiable-entries assertion is dropped. The port declares entries: [], so the runner checks nothing about the exception content and the test only verifies that some solver exception is raised.

Evidence: Upstream L356-L362 asserts entries [("numpy=1.5",), ("scipy==0.12.0b1", "numpy[version='1.6.*|1.7.*']")] via assert_unsatisfiable (L227-L238), which compares them whenever the exception type is exactly UnsatisfiableError. Port basic.yaml L4999-L5000 has 'exception: UnsatisfiableError' with 'entries: []', and install.py L373-L390 skips all content checks when error_info['entries'] is empty.

### B052

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1`

Harness issue. The declared exception class is never enforced. test_unsatisfiable always accepts any of the four exception types, and error_info['exception'] is computed but never read, so B052 would pass if classic raised ResolvePackageNotFound where upstream requires UnsatisfiableError. The same laxity applies to B053, B054, B054b, B056, B056b, B057, and B057b, whose upstream contexts accept only their stated types or pairs.

Evidence: Upstream L354 is 'with pytest.raises(UnsatisfiableError)' (subclasses included). install.py L356-L363 uses pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError)) for every unsatisfiable test, and no assertion compares exc_info.value against EXCEPTION_MAPPING[type(test.error)] from install.py L225-L227. With entries: [] every match-case branch degenerates to no check.

### B053

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::2`

Upstream's classic-solver unsatisfiable-entries assertion is dropped, as in B052. The port declares entries: [] and so verifies only that an exception is raised.

Evidence: Upstream L366-L373 asserts entries [("numpy=1.5", "nose", "python=3.3"), ("numpy=1.5", "python[version='2.6.*|2.7.*']"), ("python=3",)]. Port basic.yaml L5018-L5019 has 'exception: UnsatisfiableError' with 'entries: []', which the runner treats as no content check (install.py L373-L390).

### B054b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::3`

The port adds a content assertion upstream does not make. For the PackagesNotFoundError branch upstream asserts nothing about the exception, since bad_deps is only checked when the type is ResolvePackageNotFound. The port declares an entry, so the runner asserts the error's package names equal {numpy}. This is consistent with the scenario but could fail where upstream passes if libmamba's error content changed.

Evidence: Upstream L375-L380: content check guarded by 'if exc_info.type is ResolvePackageNotFound'. Port basic.yaml L5063-L5064 declares entries "numpy[version='1.5.*,1.6.*']" and install.py L396-L409 asserts actual_names == expected_names for PackagesNotFoundError.

### B056

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent::1`

Invented input. Upstream solves against a channel whose repodata is empty, since test_nonexistent never sets env.repo_packages. The port supplies the fully populated channel-1, so it tests a lookup miss in a populated index rather than an empty channel. The raised exception family is the same, so the outcome does not flip.

Evidence: Upstream L599-L603 contains no 'env.repo_packages =' assignment, and SimpleEnvironment.__init__ (solver_helpers.py L81) defaults repo_packages to [], producing empty repodata for the 'test' channel. Port basic.yaml L5107 sets 'channels: channel-1' with 'specs_to_add: "notarealpackage 2.0*"'.

### B056b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent::1`

Same invented input as B056. The libmamba variant also runs against populated channel-1 where upstream's channel repodata is empty.

Evidence: Upstream L599-L601 with repo_packages defaulting to [] (solver_helpers.py L81). Port basic.yaml L5128 sets 'channels: channel-1'.

### B057

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent::2`

Invented input, and the description's rationale is the port's, not upstream's. Upstream installs 'numpy 1.5' against an empty channel, so the failure is a missing package name. The port uses channel-1, where the failure is instead a missing exact version among existing numpy 1.5.1 builds. The description ('numpy 1.5.0 does not exist, only 1.5.1 does') is true of channel-1 but does not describe why upstream raises.

Evidence: Upstream L602-L603 runs env.install("numpy 1.5") with repo_packages never set (empty repodata, solver_helpers.py L81). Port basic.yaml L5146 sets 'channels: channel-1' and the description at L5141-L5143 gives the version-miss rationale.

### B057b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent::2`

Same invented input and description rationale as B057, for the libmamba variant.

Evidence: Upstream L602-L603 with an empty channel. Port basic.yaml L5167 sets 'channels: channel-1' and the description at L5159-L5161 repeats the version-miss rationale.

### B058

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_simple`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: []. With empty entries the harness also never enforces the exception type, since its pytest.raises accepts all four mapped exception types and the declared type is only checked through entry matching.

Evidence: Upstream lines 391-397 assert self.assert_unsatisfiable(exc_info, [("a", "c[version='>=1,<2']"), ("b", "c[version='>=2,<3']")]), which runs for the classic solver (exact UnsatisfiableError type). basic.yaml lines 5188-5190 give only 'exception: UnsatisfiableError' with 'entries: []', and install.py line 373 ('if error_info.get("entries"):') skips all entry checks, while lines 356-363 accept any of the four exception classes.

### B059

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_chain`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 520-526 assert entries [("a", "b", "c[version='>=1,<2']"), ("e", "c[version='>=2,<3']")]. basic.yaml lines 5207-5209 give 'exception: UnsatisfiableError' with 'entries: []', so install.py's classic-solver check at line 376 ('set(unsatisfiable) == set(error_info["entries"])') never runs.

### B060

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_expand_single`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 575-581 assert entries [("b", "d[version='>=1,<2']"), ("c", "d[version='>=2,<3']")]. basic.yaml lines 5224-5226 give 'exception: UnsatisfiableError' with 'entries: []', so no chain or type-specific check executes in install.py.

### B061

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_missing_dep`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 591-597 assert entries [("a", "b"), ("b",)]. basic.yaml lines 5242-5245 give 'exception: UnsatisfiableError' with 'entries: []', so install.py skips the classic-solver entry comparison entirely.

### B062

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_shortest_chain_1`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 421-429 assert entries [("a", "c[version='<1.3.0']"), ("a", "d", "c[version='>=0.8.0']"), ("b", "c"), ("c=1.3.6",)]. basic.yaml lines 5263-5265 give 'exception: UnsatisfiableError' with 'entries: []', so none of the four chains is checked.

### B063

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_shortest_chain_2`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 447-455 assert entries [("a", "c[version='>=0.8.0']"), ("a", "d", "c[version='<1.3.0']"), ("b", "c"), ("c=1.3.6",)]. basic.yaml lines 5282-5285 give 'exception: UnsatisfiableError' with 'entries: []', so none of the four chains is checked.

### B064

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_shortest_chain_3`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 475-482 assert entries [("a", "e", "c[version='<1.3.0']"), ("b", "c"), ("c=1.3.6",)]. basic.yaml lines 5302-5305 give 'exception: UnsatisfiableError' with 'entries: []', so none of the three chains is checked.

### B065

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_shortest_chain_4`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 498-504 assert entries [("a", "py=3.7.1"), ("py=3.6.1",)]. basic.yaml lines 5321-5324 give 'exception: UnsatisfiableError' with 'entries: []', so neither chain is checked.

### B067

Upstream: `tests/core/test_solve.py::test_downgrade_python_prevented_with_sane_message::2`

Upstream asserts specific error-message snippets for both solvers, but the port checks only that UnsatisfiableError is raised, with no entry or message assertions.

Evidence: Upstream L3363-L3383: after pytest.raises(UnsatisfiableError), classic asserts snippets 'incompatible with the existing python installation in your environment:', '- scikit-learn==0.13 -> python=2.7', 'Your python: python=2.6', and libmamba asserts 'Encountered problems while solving', 'Pins seem to be involved in the conflict...', plus regexes. The port (basic.yaml lines 3018-3020) has only 'exception: UnsatisfiableError' with 'entries: []' and no message_includes, and the harness then performs no assertion beyond the exception type. The classic literal snippets could have been carried as message_includes.

### B068

Upstream: `tests/core/test_solve.py::test_downgrade_python_prevented_with_sane_message::3`

Same weakening as B067: upstream's per-solver error-message snippet assertions are dropped, leaving only the exception-type check.

Evidence: Upstream L3392-L3411: pytest.raises(UnsatisfiableError) followed by classic snippets '- unsatisfiable-with-py26 -> python=2.7', 'Your python: python=2.6', and libmamba snippets including 'unsatisfiable-with-py26'. The port (basic.yaml lines 3044-3046) has 'entries: []' and no message_includes, so none of these are asserted.

### B083

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible::2`

Upstream accepts only PackagesNotFoundError or ResolvePackageNotFound, but the harness's test_unsatisfiable catches four exception types and never asserts that the raised class matches the YAML-declared 'exception: ResolvePackageNotFound', so the port would also pass on UnsatisfiableError or SpecsConfigurationConflictError and the declared per-solver class is documentation only.

Evidence: Upstream test_solve.py L3851: 'with pytest.raises((PackagesNotFoundError, ResolvePackageNotFound)):'. Port install.py L356-L363: 'pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError))' with no subsequent check that type(exc_info.value) equals the mapped class, and with 'entries: []' (basic.yaml L4709) every branch of the match statement is a no-op.

### B083

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible::1`

Upstream's first solver invocation (stage ::1, the ValueError case) is neither ported anywhere in the repo nor mentioned in the descriptions of B083 or B083b, so a stage of this multi-stage upstream test is silently dropped. ValueError is not expressible in the harness's EXCEPTION_MAPPING, which explains the omission, but nothing documents it.

Evidence: Upstream test_solve.py L3839-L3842: 'specs = (MatchSpec("accelerate=*=np17*"), MatchSpec("accelerate=*=np16*"))' inside 'with pytest.raises(ValueError):', failing at solver instantiation. A grep of conda-solver-tests/ and tests/ finds only node ids '::2' and '::3' for this test (basic.yaml L4694, L4714, L4734, L4754), and the B083/B083b descriptions (L4698-L4700, L4718-L4720) do not mention the dropped stage.

### B083b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible::2`

Same harness weakening as B083: upstream tolerates exactly two exception classes, the ported runner accepts four and never verifies the declared 'exception: PackagesNotFoundError', so the libmamba variant's declared class is unenforced.

Evidence: Upstream test_solve.py L3851 versus install.py L356-L363, with 'entries: []' at basic.yaml L4729 making all post-raise checks no-ops.

### B084

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible::3`

Same harness weakening: upstream's stage 3 accepts only PackagesNotFoundError or ResolvePackageNotFound, the ported runner accepts four exception classes and does not enforce the declared 'exception: ResolvePackageNotFound'.

Evidence: Upstream test_solve.py L3857: 'with pytest.raises((PackagesNotFoundError, ResolvePackageNotFound)):' for specs '*np15*' and '*py33*'. Port install.py L356-L363 and basic.yaml L4747-L4749 with empty entries.

### B084b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible::3`

Same harness weakening as B084 for the libmamba variant: the declared 'exception: PackagesNotFoundError' is never enforced and the accepted exception set is wider than upstream's.

Evidence: Upstream test_solve.py L3857 versus install.py L356-L363, basic.yaml L4767-L4769 with empty entries.

### B088

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_any_two_not_three (stage 4)`

The port drops upstream's classic-solver conflict-chain assertion by declaring entries: [], and with empty entries the harness does not enforce the specific exception type either.

Evidence: Upstream lines 556-563 assert entries [("a", "d[version='>=1,<2|>=2,<3']"), ("b", "d[version='>=1,<2|>=3,<4']"), ("c", "d[version='>=2,<3|>=3,<4']")]. basic.yaml lines 5423-5425 give 'exception: UnsatisfiableError' with 'entries: []', so none of the three chains is checked.

### B094

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_no_features::1`

The entry has no 'solvers:' restriction, so it runs and asserts the full final state under libmamba, while upstream skips test_no_features entirely for the libmamba solver. Sibling ports of other skipped feature tests (B137, B138, B140) correctly carry 'solvers: classic'. On libmamba the port asserts behaviour upstream never tests.

Evidence: Upstream tests/test_solvers.py L23-L39 (TestLibMambaSolver.tests_to_skip) lists 'test_no_features' under the reason 'conda-libmamba-solver does not support features'. Port basic.yaml L4771-L4800 contains no solvers key, so plugin.py parametrises it for both --conda-solver values.

### B105

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent_deps::5`

The declared exception type is not actually enforced by the runner, and the accepted exception set is wider than upstream's. Upstream stage 5 accepts only (ResolvePackageNotFound, UnsatisfiableError). The port's runner accepts all four mapped exception types, and because entries is empty no type-specific assertion runs, so B105 (classic, declared ResolvePackageNotFound) would also pass on UnsatisfiableError, PackagesNotFoundError, or SpecsConfigurationConflictError.

Evidence: Upstream solver_helpers.py line 753: 'with pytest.raises((ResolvePackageNotFound, UnsatisfiableError)):' then 'env.install("mypackage 1.1")'. Runner install.py lines 356-363: 'pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError))', and each match-case body only asserts under 'if error_info.get("entries")', which is falsy for basic.yaml line 5744 'entries: []', so the YAML line 5743 'exception: ResolvePackageNotFound' only selects an EXCEPTION_MAPPING key and is never checked against the raised type.

### B105b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent_deps::5`

Same harness weakness as B105: the declared UnsatisfiableError for libmamba is not enforced, and the port accepts two exception types (PackagesNotFoundError, SpecsConfigurationConflictError) that upstream's pytest.raises tuple would reject.

Evidence: Upstream solver_helpers.py line 753 accepts only '(ResolvePackageNotFound, UnsatisfiableError)'. Runner install.py lines 356-363 accept the four-type tuple, and basic.yaml line 5768 'entries: []' means the UnsatisfiableError match-case at install.py lines 371-390 asserts nothing, so basic.yaml line 5767 'exception: UnsatisfiableError' is never verified against the actual exception.

### B110

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::7 (labelled ::3 in the port)`

The node_id stage number is wrong. B110 ports the seventh solver invocation of test_timestamps_and_deps, the final unconstrained install, but its provenance says ::3, which collides with B174. B174 correctly uses ::3 for the inner libpng 1.2.* solve, and B175 to B177 use ::4 to ::6, so ::7 is the free and correct number for B110. The sibling test_nonexistent_deps entries (::1 to ::7) confirm the invocation-numbering scheme.

Evidence: basic.yaml line 5879 has 'node_id: conda/testing/solver_helpers.py::SolverTests::test_timestamps_and_deps::3' for the entry whose input is 'specs_to_add: ts_mypackage' alone, which corresponds to upstream line 643 'assert env.install("mypackage") == records_15', the seventh env.install call. basic.yaml line 5986 (B174) also carries '::3', for upstream line 634's inner 'env.install("libpng 1.2.*", as_specs=True)', which really is invocation 3.

### B113

Upstream: `tests/core/test_solve.py::test_prune_1::1`

Upstream carries an active strict xfail on libmamba, but the port restricts the test to classic via solvers, so on libmamba it is skipped instead of strict-xfailed. The upstream guarantee that the test fails under libmamba (an XPASS would be an error) is lost. The same choice is made for the stage-2 port (B160), so it is consistent, but it maps an active strict xfail to a skip rather than to xfail_solvers.

Evidence: Upstream lines 461-468: 'def test_prune_1(tmpdir, request): request.applymarker(pytest.mark.xfail(context.solver == "libmamba", reason="Features not supported in libmamba", strict=True))'. Ported basic.yaml line 1747 has 'solvers: classic', which plugin.py pytest_generate_tests turns into a skip mark ('only applicable to solvers: classic') on a libmamba run, not a strict xfail.

### B117

Upstream: `tests/core/test_solve.py::test_update_prune_3::2`

The port marks stage 2 with xfail_solvers: libmamba (strict xfail), but upstream never executes this stage under libmamba, because the function-level strict xfail already fails at the stage-1 order assertion. There is therefore no upstream expectation that this stage fails under libmamba. The sibling port B115 handles the identical situation in test_update_prune_2 with solvers: classic and explains the unreachability. A strict xfail here risks an XPASS failure if libmamba prunes to the expected 8-record state, which is the same solve B074 expects libmamba to produce for numpy plus python=2.7.3.

Evidence: Upstream at 03329e0, tests/core/test_solve.py L674-755: the xfail is applied once at function level (L677-683, 'request.applymarker(pytest.mark.xfail(context.solver == "libmamba", reason="Features not supported in libmamba", strict=True))') and under libmamba the test fails at the stage-1 'assert convert_to_dist_str(final_state_1) == order' before the second get_solver block is reached. The ported entry (basic.yaml L2665-2720) has 'xfail_solvers: libmamba' and 'xfail_reason: "Features not supported in libmamba"', whereas B115 (basic.yaml L2581) uses 'solvers: classic' with a description stating 'there is no libmamba expectation to port'.

### B125

Upstream: `tests/core/test_solve.py::test_indirect_dep_optimized_by_version_over_package_count::2`

The port asserts an exact 61-record final state on both solvers, while upstream stage 2 deliberately asserts only three conditional attribute checks and never asserts the full solution. Any incidental difference in the solution (extra or substituted packages that still satisfy anaconda 1.5.0 and zeromq build 1) passes upstream but fails the port. The recorded list is consistent with the exact pins of anaconda-1.5.0-np17py33_0 in the pinned index, so it is plausible, but the assertion is invented and much stronger than upstream, and B125 is a terminal stage so no chaining requires it.

Evidence: Upstream lines 3811-3817 are the only assertions: 'for prec in final_state: if prec.name == "anaconda": assert prec.version == "1.5.0" elif prec.name == "zeromq": assert prec.build_number == 1 elif prec.name == "_dummy_anaconda_impl": assert prec.version == "2.0"'. Ported basic.yaml lines 1976-2037 pin the full final_state from 'channel-1/${{ arch }}::freetype-2.4.10-0' through 'channel-1/${{ arch }}::anaconda-1.5.0-np17py33_0'.

### B133

Upstream: `tests/core/test_solve.py::test_features_solve_1::1`

The ported final_state is listed in alphabetical order rather than upstream's asserted solver order, so the documented expectation does not match the order upstream requires. It only passes at runtime because the runner compares sets, meaning upstream's exact-order assertion is not reproduced at all for this test.

Evidence: Upstream order tuple at tests/core/test_solve.py L3014-L3023 is nomkl, libgfortran, openssl, readline, sqlite, tk, zlib, openblas, python, numpy, asserted with tuple equality at L3026. The port at conda-solver-tests/basic.yaml lines 4384-4393 lists libgfortran-3.0.0-1, nomkl-1.0-0, numpy-1.13.1-py27_nomkl_0, openblas-0.2.19-0, openssl-1.0.2l-0, python-2.7.13-0, readline-6.2-2, sqlite-3.13.0-0, tk-8.5.18-0, zlib-1.2.11-0, an alphabetical order that differs from upstream's.

### B133

Upstream: `tests/core/test_solve.py::test_features_solve_1::1`

Upstream carries an active strict xfail for libmamba on this function, which runs and must fail under libmamba. The port converts it to a skip (solvers: classic) on a stage that is reachable under libmamba, and the sibling B134 does the same, so the upstream expectation that libmamba fails this test is dropped from the ported set entirely. The stack's own convention, seen in B129, is to carry a function-level strict xfail as xfail_solvers on the failing stage.

Evidence: Upstream tests/core/test_solve.py L2993-L2999: request.applymarker(pytest.mark.xfail(context.solver == "libmamba", reason="Features not supported in libmamba", strict=True)) with no run=False, so the function executes and must fail under libmamba. The port at conda-solver-tests/basic.yaml line 4372 has 'solvers: classic', which plugin.py turns into a skip, and B134 (line 4405) is also 'solvers: classic'.

### B134

Upstream: `tests/core/test_solve.py::test_features_solve_1::2`

Upstream carries an active strict xfail for libmamba, but the port converts it into a skip via 'solvers: classic' instead of 'xfail_solvers: libmamba', so the upstream guarantee that the test fails under libmamba is dropped.

Evidence: Upstream test_solve.py L2993-L2999: 'request.applymarker(pytest.mark.xfail(context.solver == "libmamba", reason="Features not supported in libmamba", strict=True))'. Port basic.yaml L4405 'solvers: classic' with no xfail_solvers, which plugin.py turns into a skip mark rather than a strict xfail.

### B134

Upstream: `tests/core/test_solve.py::test_features_solve_1::2`

Upstream asserts the exact solver-produced order of the 18-record final state, but the port cannot check order: the YAML lists the records alphabetically and the runner's comparison degrades to set equality, so an order regression can never be caught.

Evidence: Upstream test_solve.py L3033-L3056 builds an ordered tuple starting 'channel-4::blas-1.0-openblas', 'channel-4::ca-certificates-2018.03.07-0', 'channel-2::libffi-3.2.1-1' and asserts 'convert_to_dist_str(final_state_1) == order', where helpers.py L726-L727 returns a tuple, an ordered comparison. Port basic.yaml L4417-L4434 is sorted alphabetically starting with the two channel-2 records, and install.py L292 compares an IndexedSet with a plain list, which boltons IndexedSet.__eq__ evaluates as 'set(self) == set(other)' (verified empirically: IndexedSet(['b','a']) == ['a','b'] is True).

### B140

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unintentional_feature_downgrade`

Upstream asserts only two membership facts about the solution, but the port pins the entire 11-record final state, asserting much that upstream does not guarantee. The upstream-checked facts are preserved and implied by the exact list.

Evidence: Upstream solver_helpers.py L826-L827: 'assert "test::scipy-0.11.0-np17py33_x0" not in records' and 'assert "test::scipy-0.11.0-np17py33_3" in records', nothing else. Port basic.yaml L4678-L4689 pins 11 records including distribute, numpy, pip, python, and the full 3.3 stack.

### B143

Upstream: `tests/core/test_solve.py::test_no_update_deps_1::3`

Same harness weakening as B046: upstream requires UnsatisfiableError specifically for this stage, but the port's runner accepts any of four exception types and, with entries empty, performs no type or content check on the raised exception beyond membership in that tuple.

Evidence: Upstream line 2654: 'with pytest.raises(UnsatisfiableError):' around 'solver.solve_final_state()'. Ported basic.yaml lines 2192-2194 declare 'exception: UnsatisfiableError' with 'entries: []', and install.py test_unsatisfiable (lines 356-363) raises on the four-type tuple without asserting the declared class.

### B145a

Upstream: `tests/core/test_solve.py::test_update_prune_5::1`

The expected 14-record final_state has no upstream counterpart. Upstream stage 1 calls solve_final_state without asserting anything about the solution, and its only stage-1 assertion is a stdout check, which the port drops silently, its description does not mention the drop or that the record list is pinned from observed solver behaviour rather than from upstream.

Evidence: Upstream at 03329e0, tests/core/test_solve.py L832-836: 'with get_solver(tmpdir, specs) as solver: final_state_1 = solver.solve_final_state()' followed only by 'out, _ = capsys.readouterr(); assert "Updating numexpr is constricted by" not in out'. There is no order assertion anywhere in the function. The ported entry (basic.yaml L2721-2753) asserts an exact ordered final_state of 14 records starting 'channel-1/${{ arch }}::mkl-11.0-np17py27_p1' including scipy and scikit-learn, none of which can be checked against upstream.

### B145b

Upstream: `tests/core/test_solve.py::test_update_prune_5::1`

Same issue as B145a for the libmamba variant. The expected 10-record final_state is invented, since upstream never asserts the stage-1 solution under any solver, and the stage-1 stdout assertion is dropped without mention in the description.

Evidence: Upstream at 03329e0, tests/core/test_solve.py L832-836 makes no assertion on final_state_1, only 'assert "Updating numexpr is constricted by" not in out'. The ported entry (basic.yaml L2755-2782) asserts an exact ordered 10-record final_state including 'channel-1/${{ arch }}::numpy-1.7.1-py27_0', which has no upstream basis and describes the libmamba solution as 'keeps only the direct dependencies of the requested numexpr build', a claim upstream never makes.

### B146a

Upstream: `tests/core/test_solve.py::test_update_prune_5::2 (prune=True)`

Upstream's only assertion for this stage is that the constriction diagnostic is absent from stdout. The port substitutes an exact ordered 10-record final_state that upstream never asserts. The description accounts for the stdout part being unrepresentable but does not state that the final_state itself is pinned from solver behaviour rather than from upstream, unlike B178 which says 'pinned from solver behaviour' explicitly for the same situation.

Evidence: Upstream at 03329e0, tests/core/test_solve.py L843-853: 'solver.solve_final_state(prune=prune)' with no state assertion, then 'assert ("Updating numexpr is constricted by" in out) is solve_using_prefix_data' where solve_using_prefix_data is False for prune=True. The ported entry (basic.yaml L2784-2833) asserts an exact final_state of 10 records including 'channel-1/${{ arch }}::numexpr-2.0.1-np17py27_p2' and 'channel-1/${{ arch }}::numpy-1.7.1-py27_p0', none of which appear in any upstream assertion.

### B147

Upstream: `tests/core/test_solve.py::test_update_prune_5::2 (prune=False)`

Upstream carries an active strict xfail for libmamba on the no-prune case, but the port maps it to a skip via 'solvers: classic', so the libmamba no-prune case is neither run nor verified to fail anywhere.

Evidence: Upstream L820-L826: request.applymarker(pytest.mark.xfail(context.solver == "libmamba" and not prune, reason="Features not supported in libmamba", strict=True)) with no run=False, so upstream executes libmamba and verifies it fails. The port (basic.yaml line 2889) has 'solvers: classic', which the plugin turns into a skip. The stated porting convention maps an active strict xfail to xfail_solvers. Mitigating context: the upstream assertion that fails under libmamba is the stdout diagnostic, which the port cannot represent, and the description discloses the upstream xfail.

### B153

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_channel_priority::3`

The port changes the channel-priority input from upstream's literal setting. Upstream stage 3 sets CONDA_CHANNEL_PRIORITY=True, which conda maps to flexible, the same value as stage 1 where the same install succeeds, so under the literal input no UnsatisfiableError could be raised. The port uses 'channel_priority: strict' to realise the unsatisfiability the upstream author evidently intended (the whole upstream test is xfail because the env var has no effect). The description presents strict as the scenario without noting that upstream's input was True/flexible, so the input substitution is undisclosed.

Evidence: Upstream at 03329e0f, conda/testing/solver_helpers.py line 1048: 'monkeypatch.setenv("CONDA_CHANNEL_PRIORITY", "True")' before the pytest.raises block, versus line 1036 setting the identical value for the succeeding stage 1 install. Port: basic.yaml line 3384 'channel_priority: strict', description lines 3376-3380 which mention only 'With strict priority'.

### B172

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_circular_dependencies::2`

The port drops the index-1 packages from the solver's channels. Upstream places index_packages(1) plus the two synthetic records in the repo, but the port lists only channel-7. The outcome is unaffected because package1 and package2 depend only on each other, yet the upstream input is not fully represented.

Evidence: Upstream line 831: 'env.repo_packages = index_packages(1) + [' followed by the package1 and package2 records. basic.yaml line 5959: 'channels: channel-7' with no channel-1. Other entries from the same helper file, such as B108 at lines 5844-5846, do carry both channel-7 and channel-1.

### B173

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_circular_dependencies::3`

Same channel omission as B172. Upstream's repo contains index_packages(1) plus the two synthetic records, while the port gives the solver only channel-7. Outcome-neutral here, but the upstream input set is trimmed.

Evidence: Upstream line 831: 'env.repo_packages = index_packages(1) + ['. basic.yaml line 5976: 'channels: channel-7' only, for 'specs_to_add: package2'.

### I001

Upstream: `tests/core/test_solve.py::test_pinned_1 (stage 1, the numpy solve)`

The first solver invocation of test_pinned_1 is neither ported nor accounted for in any description. Upstream solves numpy from channel-1 before any pins are set and asserts a full 8-record state ending in numpy-1.7.1-py33_0. The ported series starts at the system=5.8=0 solve, so that assertion is silently dropped. No other YAML file carries a test_pinned_1 provenance, and no description in integration.yaml mentions the stage.

Evidence: Upstream tests/core/test_solve.py L2357-L2374 at commit 03329e0f: 'specs = (MatchSpec("numpy"),)' then 'assert convert_to_dist_str(final_state_1) == order' with order ending 'channel-1::python-3.3.2-0', 'channel-1::numpy-1.7.1-py33_0'. integration.yaml I001 (lines 3-17) ports the later 'specs = (MatchSpec("system=5.8=0"),)' solve (upstream L2377-L2384), and no entry or description covers the numpy stage. The dropped state is not used downstream, since upstream rebinds final_state_1 at the system solve.

### I013

Upstream: `tests/core/test_solve.py::test_freeze_deps_1::4 (also affects I004, I015)`

The harness weakens the exception-type assertion for unsatisfiable tests. Upstream pins the exact exception with pytest.raises(UnsatisfiableError), but the harness catches a union of four exception types and, because I013's entries list is empty, performs no content check at all on the matched exception. I013 and I015 would therefore pass vacuously if the solver raised, say, PackagesNotFoundError instead of UnsatisfiableError, and I004 would pass if UnsatisfiableError were raised instead of SpecsConfigurationConflictError.

Evidence: Upstream L3138-L3146: 'with pytest.raises(UnsatisfiableError): ... solver.solve_for_diff()'. Harness install.py test_unsatisfiable (lines 356-363) uses 'pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError))', and each match arm guards its checks with 'if error_info.get("entries")', which is falsy for I013's 'entries: []' (integration.yaml line 501), so a wrong exception type from the union still passes.

### I017b

Upstream: `tests/core/test_solve.py::test_python2_update::2 (libmamba branch)`

Upstream deliberately relaxes the libmamba assertion to a three-package subset check because libmamba's solution differs from classic and was not considered stable enough to pin. The port instead asserts the entire 31-record final state and its exact (alphabetical) order, a strictly stronger assertion that can fail where upstream would pass if the libmamba solution drifts. The description discloses that the full state is 'pinned from solver behaviour', and the pinned state does contain upstream's three required records plus the cryptography-2.3/cryptography-vectors difference upstream describes, so it does not contradict upstream today.

Evidence: Upstream L2026-L2044: 'we only check some packages' and 'assert set(important_parts).issubset(set(full_solution))' with important_parts limited to python-3.7.0-hc3d631a_0, conda-4.5.10-py37_0, pycosat-0.6.3-py37h14c3975_0. integration.yaml I017b lines 780-811 assert a full 31-record final_state, which the harness compares for exact content and order (install.py lines 288-292).

### C003

Upstream: `tests/core/test_solve.py::test_cuda_fail_1`

The port drops all of upstream's error-message assertions and only checks that an UnsatisfiableError is raised. Upstream asserts solver-specific message content on both branches.

Evidence: Upstream L283-L306 at 03329e0f: for libmamba, 'assert any(msg in exc_msg for msg in possible_messages)' over two 'nothing provides __cuda >=9.0 needed by cudatoolkit-9.0-0' style messages, and for classic an exact full-message equality including "cudatoolkit -> __cuda[version='>=10.0|>=9.0']" and 'Your installed version is: 8.0'. Port conda-solver-tests/cuda.yaml L51-L53 has only 'exception: UnsatisfiableError' with 'entries: []' and no message_includes, so with empty entries the runner (install.py L370-L390) asserts nothing about the message.

### C003

Upstream: `tests/core/test_solve.py::test_cuda_fail_1 (harness behaviour, applies equally to C004 test_cuda_fail_2 and C007 test_solve_msgs_exclude_vp)`

The runner never enforces the declared exception type. Upstream pins pytest.raises(UnsatisfiableError), but the harness accepts any of four exception types and, because entries is empty, would silently pass if a different one were raised.

Evidence: Upstream L280 'with pytest.raises(UnsatisfiableError) as exc'. Harness pytest_conda_solvers/base_tests/install.py L356-L363 uses 'pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError))' and the following match statement dispatches on the actual type without ever asserting it equals error_info['exception'], so a PackagesNotFoundError raise would pass C003, C004, and C007.

### C004

Upstream: `tests/core/test_solve.py::test_cuda_fail_2`

As with C003, the port drops all of upstream's error-message assertions and only checks the exception type.

Evidence: Upstream L319-L341: libmamba branch asserts one of two 'nothing provides __cuda ... needed by cudatoolkit...' messages, classic branch asserts exact equality with a message ending 'Your installed version is: not available'. Port cuda.yaml L69-L71 has 'exception: UnsatisfiableError' with 'entries: []' and no message checks.

### C006

Upstream: `tests/core/test_solve.py::test_cuda_glibc_sat`

Upstream restricts this test to Linux, but the port runs it on every platform. On non-Linux hosts the __glibc virtual package is never generated, so CONDA_OVERRIDE_GLIBC is inert there and the test passes vacuously without exercising the glibc constraint upstream intended to test.

Evidence: Upstream L390 carries '@pytest.mark.skipif(not on_linux, reason="linux-only test")' (also outside the permalink range L391-L401). Port cuda.yaml L91-L108 has no restriction, and the harness sets no CONDA_SUBDIR, so conda/plugins/virtual_packages/linux.py bails via 'if not context.subdir.startswith("linux-"): return' on macOS and Windows, leaving no __glibc for the override to apply to while cuda-glibc-10.0-0 still installs because its __glibc entry is only a constrains.

### S001

Upstream: `tests/core/test_solve.py::test_determine_constricting_specs_conflicts`

The port strengthens upstream's assertion from name membership to exact list equality including the constricting MatchSpec and list length. Verified consistent with the pinned implementation, but a differently-formatted yet valid result from another backend would fail the port while passing upstream.

Evidence: Upstream L3534-L3535: 'assert any(i for i in constricting if i[0] == "mypkgnot")' with no check of the spec or list size. Port constricting_specs.yaml L43-L46 expects exactly [('mypkgnot', 'mypkg==0.1.0')] and the runner (install.py L344) asserts full list equality. The pinned implementation returns [('mypkgnot', MatchSpec('mypkg 0.1.0'))] and MatchSpec normalisation makes that equal to 'mypkg==0.1.0' (checked empirically).

### S002

Upstream: `tests/core/test_solve.py::test_determine_constricting_specs_conflicts_upperbound`

Same strengthening as S001: upstream only asserts that some constriction is named mypkgnot, the port asserts the exact single-element list including the <=0.1.1 spec.

Evidence: Upstream L3573-L3574: 'assert any(i for i in constricting if i[0] == "mypkgnot")'. Port constricting_specs.yaml L89-L92 expects exactly [('mypkgnot', 'mypkg<=0.1.1')] via full list equality in install.py L344.

### S003

Upstream: `tests/core/test_solve.py::test_determine_constricting_specs_multi_conflicts`

Upstream asserts only that constrictions named mypkgnot and notmypkg exist. The port asserts an exact ordered two-element list including both specs, and the ordering (mypkgnot before notmypkg) is an implementation detail of iteration over solution_precs that upstream never pins down.

Evidence: Upstream L3627-L3628: 'assert any(i for i in constricting if i[0] == "mypkgnot")' and 'assert any(i for i in constricting if i[0] == "notmypkg")'. Port constricting_specs.yaml L149-L154 expects [('mypkgnot', 'mypkg<=0.1.1'), ('notmypkg', 'mypkg==0.1.1')] in that order, and the runner's '==' on lists is order-sensitive.

## Notes

Cosmetic or documentation-level issues: description claims, permalink ranges, redundant fields, and inert input differences. Ordered by test id.

### B004

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_anaconda_nomkl (also B005, B006, B007, B007b from the same fixture)`

Upstream's SolverTests fixture bakes pip into python's depends (index built with add_pip=True), whereas the port runs B004 through B007b with add_pip false, so CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY is false and python has no pip edge. Inert for B004 because the anaconda metapackage depends on pip directly, and B003 does set add_pip: true for the same fixture, making the omission inconsistent.

Evidence: Upstream solver_helpers.py index_packages calls get_index_r_1(context.subdir), whose signature at helpers.py line 314 defaults add_pip=True, and _get_index_r_base processes repodata under context._override("add_pip_as_python_dependency", add_pip). SimpleEnvironment writes 'depends' into its repodata (REPO_DATA_KEYS). Ported B004 input (basic.yaml lines 92-97) has no add_pip field, so install.py get_solver sets CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY=false. channel-1_non-noarch.json shows anaconda-1.5.0-np17py27_0 depends on 'pip 1.3.1 py27_1' and 'distribute 0.6.36 py27_1', so the solution is unchanged.

### B005

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1 (applies to B006, B007, B007b too)`

Upstream's pytest.raises is specific to the expected exception, but the harness catches a union of four exception types for every unsatisfiable test and dispatches on whichever type actually arrived, so a wrong-typed exception is rejected only indirectly through the per-type payload checks rather than outright.

Evidence: Upstream solver_helpers.py lines 354 and 365: with pytest.raises(UnsatisfiableError), and line 375: pytest.raises((ResolvePackageNotFound, PackagesNotFoundError)). Port install.py lines 356-363: pytest.raises((UnsatisfiableError, PackagesNotFoundError, ResolvePackageNotFound, SpecsConfigurationConflictError)) regardless of the declared exception, followed by a match on the actual value's type, so for B005 a PackagesNotFoundError naming numpy would pass where upstream would fail.

### B007b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::3`

The entries field carries a full version constraint, but the harness's PackagesNotFoundError branch compares package names only, so the version text is decorative and only 'numpy' is checked. Upstream checks nothing at all for the PackagesNotFoundError case, so the port is marginally stricter, but the YAML overstates what is asserted.

Evidence: Ported basic.yaml lines 283-286: exception PackagesNotFoundError with entries "numpy[version='1.5.*,1.6.*']". Port install.py lines 396-409: builds expected_names from spec.name and asserts actual_names == expected_names, with an inline comment explaining that libmamba formats the constraint differently ('1.5,=1.6.*'). Upstream solver_helpers.py lines 375-380 checks bad_deps only 'if exc_info.type is ResolvePackageNotFound' and nothing for PackagesNotFoundError.

### B008

Upstream: `tests/core/test_solve.py::test_aggressive_update_packages::1 (also ::3 as B010 and ::6 as B013)`

Upstream explicitly empties aggressive_update_packages for these stages by setting the env var to an empty string, but the port either omits the field (B008) or writes a YAML null (B010, B013), which the harness drops entirely, leaving conda's default aggressive list (ca-certificates, certifi, openssl) active. Behaviourally inert here because none of those packages is in the prefix, but the input is not faithfully represented.

Evidence: Upstream test_solve.py lines 1838, 1865, and 1910: monkeypatch.setenv("CONDA_AGGRESSIVE_UPDATE_PACKAGES", "") before stages 1, 3, and 6. Ported basic.yaml: B008 has no aggressive_update_packages key, B010 line 337 and B013 line 401 have 'aggressive_update_packages:' with no value. install.py get_env_pair returns None for a None value and prepare_solver_input filters it out, so the env var is never set. conda/core/solve.py lines 575, 794, and 945 only apply aggressive specs to names already installed or tracked, and the prefixes contain only libpng and cmake.

### B025

Upstream: `tests/core/test_solve.py::test_update_all_1::1`

The port uses the libmamba form of the system spec, 'system[version=*,build=*0]', for both solvers, whereas upstream uses 'system[version=*,build_number=0]' on classic and the build=*0 form only on libmamba. Over channel-1 data (system-5.8-0 with build '0' and system-5.8-1 with build '1') both forms match the same single package, and upstream's own comment says the result should be identical, so this is cosmetic.

Evidence: Upstream test_solve.py lines 1122-1130 at commit 03329e0f: 'if context.solver == "libmamba": system_spec = "system[version=*,build=*0]" else: system_spec = "system[version=*,build_number=0]"' with the comment 'It should be the same result, but in a conda_build_form-friendly way'. basic.yaml B025 line 1106 uses 'system[version=*,build=*0]' unconditionally.

### B026

Upstream: `tests/core/test_solve.py::test_update_all_1::2`

Same as B025: the history_specs use the libmamba form 'system[version=*,build=*0]' for both solvers, where upstream's classic branch would carry 'system[version=*,build_number=0]' in history. Semantically equivalent for the channel-1 system packages.

Evidence: Upstream test_solve.py lines 1122-1130 (solver-conditional system spec, carried into history via 'history_specs=specs' at line 1156). basic.yaml B026 line 1143 uses 'system[version=*,build=*0]' in history_specs unconditionally.

### B027

Upstream: `tests/core/test_solve.py::test_update_all_1::3`

Upstream branches on context.solver for the system history spec, giving classic 'system[version=*,build_number=0]' and libmamba 'system[version=*,build=*0]'. The port uses the libmamba form for both solvers with no a/b variant, so the classic run receives a differently written spec than upstream. Behaviourally inert here: upstream's comment says the two forms give the same result, and under UPDATE_ALL conda reduces history specs to names anyway, which is why the expected output legitimately contains system-5.8-1 despite the build-0 constraint.

Evidence: Upstream at commit 03329e0f, tests/core/test_solve.py lines 1122-1129: 'if context.solver == "libmamba": ... system_spec = "system[version=*,build=*0]" else: system_spec = "system[version=*,build_number=0]"', with the comment 'It should be the same result, but in a conda_build_form-friendly way'. Ported basic.yaml line 1183: history_specs contains 'system[version=*,build=*0]' unconditionally, and the entry has no solvers restriction, so the classic run also gets the libmamba form. The same convention is applied in B025 and B026, which belong to other stages.

### B046

Upstream: `tests/core/test_solve.py::test_only_deps_2::3`

The description claims 'numba=0.5 requires numpy>=1.7', which is not true of the upstream data. Channel-1 ships numba-0.5.0-np16py27_0 depending on 'numpy 1.6*' as well as numba-0.5.0-np17py27_0 depending on 'numpy 1.7*'. The solve is unsatisfiable because the history-pinned numpy=1.5 satisfies neither variant, not because numba 0.5 requires numpy>=1.7.

Evidence: Ported basic.yaml lines 2046-2049 description: 'numba=0.5 requires numpy>=1.7'. Upstream tests/data/index.json at the pinned commit contains 'numba-0.5.0-np16py27_0.tar.bz2 | depends: [llvmpy 0.10.0, meta 0.4.2.dev, nose, numpy 1.6*, python 2.7*]'. Upstream's own comment (line 1084) says only 'fails because numpy=1.5 is in our history as an explicit spec'.

### B052

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1`

add_pip differs from upstream. SolverTests solves run with conda's default add_pip_as_python_dependency of true, which is why upstream solve expectations include pip and distribute. The unsatisfiable ports leave add_pip unset, so the runner forces CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY=false. No effect on the asserted outcome here, and the same applies to B053, B054, B054b, B056, B056b, B057, and B057b.

Evidence: SimpleEnvironment (solver_helpers.py L52-L107) never overrides the pip setting, and upstream sets such as test_no_features L866-L876 include test::pip-1.3.1-py26_1, confirming true was in effect. install.py L67-L69 sets the variable from add_pip, which defaults to false in models.py L84, and none of the unsatisfiable entries at basic.yaml L4983-L5171 set add_pip.

### B073

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_circular_dependencies (stage 1)`

Upstream's repo for this test is index_packages(1) plus the two circular packages, but channel-7 contains only the synthetic renamed packages and none of the channel-1 index (no python, numpy, zlib, and so on). Behaviourally inert here because package1 and package2 depend only on each other, so the solve outcome is identical, but the input repo is not fully represented. Stages 2 and 3 of the upstream test are covered by B172 and B173 elsewhere in the file.

Evidence: Upstream lines 830-840: 'env.repo_packages = index_packages(1) + [helpers.record(name="package1", depends=["package2"]), ...]'. basic.yaml lines 5337-5341 use 'channels: channel-7', and channel-7_non-noarch.json (76 records) has no channel-1 index packages.

### B085

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_any_two_not_three (stage 1)`

The port asserts the complete final state in exact order, including atnt_d-1.0, where upstream asserts only that a-1.0 and b-1.0 appear in the solution. The extra content is entailed by the repo constraints (atnt_a 1.0 and atnt_b 1.0 both require atnt_d >=1,<2 and only 1.0 satisfies it), so it cannot contradict upstream, but it is a strictly stronger assertion, and the ordering is a harness convention with no upstream counterpart.

Evidence: Upstream lines 541-544: 'installed = env.install("a", "b", as_specs=True)' followed by two any(k.name/k.version) membership checks only. basic.yaml lines 5362-5365 assert the full ordered list [atnt_d-1.0-0, atnt_a-1.0-0, atnt_b-1.0-0], and install.py line 292 asserts ordered equality.

### B086

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_any_two_not_three (stage 2)`

The port asserts the complete final state in exact order, including atnt_d-2.0, where upstream asserts only that a-2.0 and c-1.0 appear in the solution. The added record is entailed by the constraints (both need atnt_d >=2,<3), so this is a strengthening rather than a contradiction.

Evidence: Upstream lines 546-548: membership checks 'any(k.name == "a" and k.version == "2.0" ...)' and 'any(k.name == "c" and k.version == "1.0" ...)' only. basic.yaml lines 5382-5385 assert the full ordered list [atnt_d-2.0-0, atnt_a-2.0-0, atnt_c-1.0-0].

### B087

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_any_two_not_three (stage 3)`

The port asserts the complete final state in exact order, including atnt_d-3.0, where upstream asserts only that b-2.0 and c-2.0 appear in the solution. The added record is entailed by the constraints (both need atnt_d >=3,<4), so this is a strengthening rather than a contradiction.

Evidence: Upstream lines 550-552: membership checks 'any(k.name == "b" and k.version == "2.0" ...)' and 'any(k.name == "c" and k.version == "2.0" ...)' only. basic.yaml lines 5402-5405 assert the full ordered list [atnt_d-3.0-0, atnt_b-2.0-0, atnt_c-2.0-0].

### B091

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_noarch_preferred_over_arch_when_version_greater_dep`

The description claims the dep package 'exists equally in arch and noarch, so arch is preferred for it', but upstream creates package2 only in the arch subdir (helpers.record default subdir is context.subdir), and the port's channel data matches upstream, so no noarch copy exists and no arch-versus-noarch preference is exercised for the dep.

Evidence: Upstream solver_helpers.py lines 1281-1284: 'helpers.record(name="package2", depends=["package1"])' with no subdir argument, so it lands only in context.subdir. Port channel-7_noarch.json contains no noarch_ver_pkg_dep entry, only channel-7_non-noarch.json has noarch_ver_pkg_dep-1.0-0. basic.yaml lines 5472-5473 state 'The dep package itself exists equally in arch and noarch, so arch is preferred for it.' The asserted final_state at line 5481 (channel-7/${{ arch }}::noarch_ver_pkg_dep-1.0-0) is still correct.

### B092

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_noarch_preferred_over_arch_when_build_greater`

The port's noarch record changes upstream's build string from '0' to '1', so the asserted dist string is noarch_build_pkg-1.0-1 where upstream's record would render package1-1.0-0 (build string '0' with build_number 1). This points at channel data rather than the YAML itself and is behaviourally neutral, since the test's discriminator is build_number, which is preserved as 1, and upstream only asserts the subdir. The same data feeds B093's expected noarch_build_pkg-1.0-1.

Evidence: Upstream solver_helpers.py lines 1296-1300: 'helpers.record(name="package1", build_number=1, subdir="noarch")' with helpers.record defaulting build="0" (conda/testing/helpers.py lines 452-457). Port channel-7_noarch.json has noarch_build_pkg-1.0-1.tar.bz2 with build '1', build_number 1. basic.yaml line 5499 asserts 'channel-7/noarch::noarch_build_pkg-1.0-1'.

### B093

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_noarch_preferred_over_arch_when_build_greater_dep`

The description claims the dep package 'is arch-preferred (equal versions in both subdirs)', but upstream's package2 exists only in the arch subdir and the port's channel data matches, so there is no noarch copy and no preference decision for the dep.

Evidence: Upstream solver_helpers.py lines 1317-1320: 'helpers.record(name="package2", depends=["package1"])' with no subdir, so arch only. Port channel-7_noarch.json has no noarch_build_pkg_dep entry, only channel-7_non-noarch.json has noarch_build_pkg_dep-1.0-0. basic.yaml lines 5510-5511 state 'The dep package itself is arch-preferred (equal versions in both subdirs).' The final_state at line 5519 is still correct.

### B105b

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_nonexistent_deps::5`

The in-description permalink for the upstream TODO cites L752-L754, but the TODO comment begins at L751, so the cited range misses the first line of the comment it references.

Evidence: Upstream solver_helpers.py line 751: '# TODO: We need UnsatisfiableError here because mamba does not', line 752: '# have more granular exceptions yet.', line 753: the pytest.raises. basic.yaml line 5758 links '.../conda/testing/solver_helpers.py#L752-L754'.

### B108

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::1`

Upstream asserts only membership of two records in the stage 1 result, while the port asserts the exact and complete final state. The strengthening is sound because channel data determines exactly those two records (libpng-1.2.50-0 has empty depends), but it is a stronger claim than upstream makes.

Evidence: Upstream lines 623-625: 'records_12 = env.install("libpng 1.2.*", "mypackage")' then 'assert "test::libpng-1.2.50-0" in records_12' and 'assert "test::mypackage-1.0-hash12_0" in records_12', membership only. basic.yaml lines 5851-5853 pin final_state to exactly [libpng-1.2.50-0, ts_mypackage-1.0-hash12_0].

### B109

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::2`

Same membership-to-full-equality strengthening as B108, for the libpng 1.5.* stage. Consistent with the channel data (libpng-1.5.13-1 has empty depends), but upstream never asserts that nothing else is present.

Evidence: Upstream lines 627-629: 'records_15 = env.install("libpng 1.5.*", "mypackage")' with two 'in records_15' membership asserts. basic.yaml lines 5872-5874 pin final_state to exactly [libpng-1.5.13-1, ts_mypackage-1.0-hash15_0].

### B124

Upstream: `tests/core/test_solve.py::test_indirect_dep_optimized_by_version_over_package_count::1`

Upstream stage 1 computes final_state_1 without asserting anything about it, so the port's full 51-record ordered final_state is derived rather than taken from upstream. The chaining convention requires some pinned state to feed B125's prefix, and the recorded list matches the exact three-part pins of anaconda-1.4.0-np17py33_0 in the pinned index (including system 5.8 build 0), so the content is forced by the data. Recording for completeness since every record in the assertion is port-invented.

Evidence: Upstream lines 3786-3788: 'specs = (MatchSpec("anaconda=1.4"),) ... final_state_1 = solver.solve_final_state()' with no assert on final_state_1. Ported basic.yaml lines 1853-1905 assert the full state ending in 'channel-1/${{ arch }}::anaconda-1.4.0-np17py33_0'. The index entry anaconda-1.4.0-np17py33_0 pins each listed dependency exactly, such as 'python 3.3.0 4' and 'system 5.8 0'.

### B130

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_accelerate::1`

Same pattern as B158. The node_id omits the ::1 stage suffix although upstream test_accelerate performs two solver invocations and the sibling test_accelerate_2 uses ::2, and the pinned 15-record state goes beyond upstream's equality-only assertion without the description declaring the pinning. The sibling entry pinning the identical state preserves the upstream equality.

Evidence: Upstream conda/testing/solver_helpers.py L289-L291: 'assert env.install("accelerate") == env.install("accelerate", MatchSpec(track_features="mkl"))' with no concrete expected state. The port's node_id at conda-solver-tests/basic.yaml line 4226 is '...SolverTests.test_accelerate' with no stage, while the sibling at line 4949 is '...SolverTests::test_accelerate::2'. The pinned state is at lines 4240-4254.

### B132

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_get_dists`

Upstream asserts only membership of two records in the solution. The port pins the entire 51-record final state and runs it on both solvers, a strengthening well beyond upstream that must hold identically for classic and libmamba. Both required memberships are present, so nothing upstream asserts is lost.

Evidence: Upstream conda/testing/solver_helpers.py L399-L403: asserts only '"test::anaconda-1.4.0-np17py33_0" in records' and '"test::freetype-2.4.10-0" in records'. The port at conda-solver-tests/basic.yaml lines 4309-4360 pins 51 records (including anaconda-1.4.0-np17py33_0 at line 4310 and freetype-2.4.10-0 at line 4317) with no solvers restriction, matching upstream's applicability but far exceeding its assertions.

### B135b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::1`

The description claims libmamba 'picks the plain builds', but the entry's own expected list still contains _p feature builds for accelerate, mkl, mkl-rt, and mkl-service. Only numpy and scipy differ from the classic variant.

Evidence: basic.yaml L4477-L4478 description versus L4487-L4490: 'accelerate-1.1.0-np17py33_p0', 'mkl-11.0-np17py33_p1', 'mkl-rt-11.0-p0', 'mkl-service-1.0.0-py33_p0'.

### B136b

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_compatible::2`

Same description inaccuracy as B135b: 'picks the plain builds' while the expected list keeps _p builds for accelerate, libnvvm, mkl, mkl-rt, mkl-service, and numbapro.

Evidence: basic.yaml L4552-L4553 description versus L4562, L4564, L4568-L4570, and L4572, such as 'accelerate-1.1.0-np17py27_p0' and 'numbapro-0.11.0-np17py27_p0'.

### B137

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_surplus_features_1`

Description wording is imprecise: 'the higher package2 build wins' is actually the higher version (2.0 over 1.0, both build 0), and package1 is a feature carrier (features: feature), not a 'surplus feature provider'. The provider with track_features is the feature package.

Evidence: Upstream solver_helpers.py L1111-L1131: feature has track_features="feature", package1 has features="feature", and the two package2 records differ in version ('1.0' versus '2.0'), not build number. Port description at basic.yaml L4593-L4594.

### B138

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_surplus_features_2`

The description claims 'the higher build number wins', but no build-number competition is exercised in either codebase. Upstream's two package2 v1.0 records share the default build string '0', collide on filename in the written repodata, and only the build_number 1 record survives, and the ported channel-9 accordingly contains a single package2-1.0-0 record with build_number 1 and no depends.

Evidence: Upstream solver_helpers.py L1146-L1158 constructs both records with record()'s default build '0' (helpers.py L452-L457), and _write_repo_packages (solver_helpers.py L173-L175) keys repodata by record.fn so the second overwrites the first. Ported channel-9_non-noarch.json holds exactly one 'package2-1.0-0.tar.bz2' with '"build_number": 1' and '"depends": []'. Port description at basic.yaml L4615-L4616.

### B139

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_install_package_with_feature`

The description ends 'Features are classic-only.' but the entry has no 'solvers:' restriction and upstream does run this test under the libmamba solver, since test_install_package_with_feature is not in TestLibMambaSolver.tests_to_skip. The sentence looks like a copy-paste from the sibling feature tests and contradicts both upstream and the entry's own configuration.

Evidence: basic.yaml L4637-L4638 description with no solvers key anywhere in L4629-L4659, versus upstream tests/test_solvers.py L23-L39 where the skip list omits test_install_package_with_feature.

### B140

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unintentional_feature_downgrade`

Upstream constructs the bad scipy record on the fly and serves it only for this test, but the port baked it into the shared channel-1 data file, so every channel-1 test now sees an extra scipy build that upstream's channel-1 index lacks. For B140 itself the effective index is faithful (index 1 plus the bad record), but this is a channel-data divergence with potential side effects on other channel-1 tests.

Evidence: Upstream solver_helpers.py L810-L822 builds bad_rec from the good scipy record with build 'np17py33_x0', build_number 0, and numpy stripped from depends, only within this test. Ported pytest_conda_solvers/data/channel-1_non-noarch.json permanently contains 'scipy-0.11.0-np17py33_x0.tar.bz2' with '"build_number": 0' and '"depends": ["python 3.3*"]'.

### B146b

Upstream: `tests/core/test_solve.py::test_update_prune_5::2 (prune=True, libmamba)`

The port asserts a full 9-record final state where upstream asserts no solver output at all for this stage, and B146b's own description, unlike B146a's and B147's, does not disclose the substitution of the stdout assertion.

Evidence: Upstream L849 discards the stage-2 result and L851-L853 assert only the absence of 'Updating numexpr is constricted by' on stdout, a diagnostic classic alone prints, so the check is vacuous under libmamba. The port (basic.yaml lines 2865-2875) pins a behaviour-derived final state. Inputs and the handoff prefix are correct: the prefix (lines 2850-2860) matches B145b's libmamba stage-1 final state record for record, and the pinned output is coherent with channel data (numexpr np17py27_p2 depends only on 'numpy 1.7*', 'python 2.7*', so mkl-rt is correctly absent).

### B147

Upstream: `tests/core/test_solve.py::test_update_prune_5::2 (prune=False)`

The port asserts a full 14-record final state that upstream never asserts: upstream discards the stage-2 solve result and checks only a stdout diagnostic.

Evidence: Upstream L849: 'solver.solve_final_state(prune=prune)' with the return value unused, then L851-L853 assert only '("Updating numexpr is constricted by" in out) is solve_using_prefix_data'. The port (basic.yaml lines 2914-2929) pins the complete ordered final state from solver behaviour. The description discloses that the stdout assertion is not representable, and the pinned state (featured extras kept, numexpr p3 swapped to p2) is a faithful proxy for 'prefix data is used without prune'.

### B148

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_channel_priority_1::1`

Upstream's stage-1 assertion is replaced: upstream expects 'channel-A::pandas-0.11.0-np16py27_0', a record that does not exist in its channel-A, under a non-strict xfail, while the port enforces a behaviour-pinned solution with pandas from channel-1.

Evidence: Upstream L955 marks the test '@pytest.mark.xfail(reason="CONDA_CHANNEL_PRIORITY does not seem to have any effect")' and L977-L979 assert 'channel-A::pandas-0.11.0-np16py27_0' in the result, though channel-A is built (L961-L970) holding only pandas 0.10.1 np17py27_0. The port (basic.yaml lines 3246-3260) asserts channel-1 pandas-0.11.0-np16py27_1 with the full ordered solution. The description discloses both the xfail and the impossible upstream assertion. Ported channel-13 data matches upstream's channel-A construction (only pandas-0.10.1-np17py27_0, depending on 'numpy 1.7*'), so the flexible-priority fallback expectation is coherent.

### B149

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_channel_priority_1::2`

Upstream never enforces this assertion (the whole method is a non-strict xfail, and it sets CONDA_CHANNEL_PRIORITY without reset_context, so the setting has no effect), while the port runs it as an enforced test on both solvers with a full pinned state.

Evidence: Upstream L955 xfail plus L980-L983: monkeypatch.setenv('CONDA_CHANNEL_PRIORITY', 'False') then assert 'channel-1::pandas-0.11.0-np16py27_1' in env.install(...). The port (basic.yaml lines 3272-3293) uses channel_priority: disabled, the correct mapping of 'False', applied through the harness's env_vars with context reset so it actually takes effect, and its pinned pandas record matches upstream's literal assertion. The description does not mention the upstream xfail, which only B148's does for the family.

### B150

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_channel_priority_1::3`

Same as B149: an assertion upstream never enforces (non-strict xfail on the whole method) is promoted to an enforced full-state test, with no mention of the xfail in this entry's description.

Evidence: Upstream L985-L989: env.repo_packages reversed to put channel-1 first, CONDA_CHANNEL_PRIORITY set to 'True', assert 'channel-1::pandas-0.11.0-np16py27_1' in the result, all under the L955 xfail. The port (basic.yaml lines 3305-3326) reverses the channels to [channel-1, channel-13] with channel_priority: flexible, the correct mapping of 'True', and its pinned pandas record matches upstream's literal assertion.

### B152

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_channel_priority::2`

This stage is ported as an unconditional pass although its upstream assertions never passed. The whole upstream test carries an active non-strict xfail because CONDA_CHANNEL_PRIORITY has no effect there, and under classic this stage is where the first assertion fails (the env stays on the default flexible priority, so a-1.0 wins instead of the expected a-2.0). The port's harness applies the priority properly and pins the intended disabled-priority outcome, which is a reasonable realisation of upstream intent, but unlike B151 and B153 this entry's description does not mention the upstream xfail or that the expected output was never verified upstream.

Evidence: Upstream at 03329e0f, conda/testing/solver_helpers.py line 991: '@pytest.mark.xfail(reason="CONDA_CHANNEL_PRIORITY does not seem to have any effect")', and lines 1042-1046 for the stage's setenv False plus a-2.0/b-2.0 asserts. Port: basic.yaml lines 3350-3367, whose description (lines 3357-3358) says only 'With priority disabled the highest versions win, all from channel-12.'

### B153

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_channel_priority::3`

The port asserts an extra conflict chain that upstream does not. Upstream's assert_unsatisfiable expects exactly [("b", "c[version='>=2,<3']")], while the port's entries also include [a, c], and the harness asserts set equality of classic's unsatisfiable attribute against both chains. The deviation is disclosed in the description ('Classic reports the a-c chain alongside the b conflict that upstream's (xfail) assertion names'), and upstream's own assertion never executed because the test xfails at stage 2, but it remains an assertion upstream does not make.

Evidence: Upstream at 03329e0f, conda/testing/solver_helpers.py line 1051: 'self.assert_unsatisfiable(exc_info, [("b", "c[version=\'>=2,<3\']")])'. Port: basic.yaml lines 3387-3389, entries '- [a, c]' and '- ["b", "c[version='>=2,<3']"]', matched by install.py line 376 'assert set(unsatisfiable) == set(error_info["entries"])'.

### B153

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_unsat_channel_priority::3`

For the libmamba solver the harness asserts error-message content that upstream never checks. Upstream's assert_unsatisfiable only inspects entries when the exception type is exactly UnsatisfiableError, so for LibMambaUnsatisfiableError it checks nothing beyond the subclass relationship. The port's harness instead requires the endpoint package names of each entry chain (a, b, and c here) to appear in the libmamba error message, a strengthening that could fail on a message-wording change even though upstream would still pass.

Evidence: Upstream at 03329e0f, conda/testing/solver_helpers.py lines 227-238: 'assert issubclass(exc_info.type, UnsatisfiableError)' then 'if exc_info.type is UnsatisfiableError:' guarding the entries comparison. Port: install.py lines 377-390, the branch where 'unsatisfiable is None' asserts 'name in message' for every chain-endpoint name derived from the YAML entries.

### B154

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_remove::1`

Upstream test_remove carries a class-level non-strict xfail about global state on top of the libmamba skip. The port (B154, and equally B155 and B156) drops the xfail and runs plainly under classic. Defensible, since the port isolates state per test and a non-strict xfail asserts nothing, but the mark is not represented and the description mentions only the libmamba skip.

Evidence: Upstream conda/testing/solver_helpers.py L1053-L1056: '@pytest.mark.xfail(reason="There is some weird global state making this test fail when the whole test suite is run")' directly above 'def test_remove' at L1057. The port entries at conda-solver-tests/basic.yaml lines 3808, 3840, and 3888 carry only 'solvers: classic' with no xfail_solvers, and B154's description (lines 3804-3807) cites only the tests/test_solvers.py#L22-L40 skip list.

### B158

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_mkl::1`

The node_id omits the ::1 stage suffix even though upstream test_mkl performs two solver invocations and the sibling entry test_mkl_2 uses the ::2 suffix form. Also, upstream asserts only that the two solves are equal, while this entry pins a concrete 14-record state without the description declaring it as pinned from solver behaviour. The equality itself is preserved through the sibling entry pinning the identical state.

Evidence: Upstream conda/testing/solver_helpers.py L283-L285: 'assert env.install("mkl") == env.install("mkl 11*", MatchSpec(track_features="mkl"))' with no concrete expected state. The port's node_id at conda-solver-tests/basic.yaml line 4194 is 'conda/testing/solver_helpers.py::SolverTests.test_mkl' with no stage, while the sibling at line 4913 is '...SolverTests::test_mkl::2'. The pinned state is at lines 4208-4221.

### B161

Upstream: `tests/core/test_solve.py::test_remove_with_constrained_dependencies::2`

Upstream only asserts that nothing is linked and that conda-build, conda, and pycosat appear in the unlink set. The port pins the full 28-record unlink list, and it runs on both solvers, so the strengthened assertion must hold identically for classic and libmamba where upstream deliberately checked only containment. The strengthening is declared in the description, so this is informational.

Evidence: Upstream tests/core/test_solve.py L2874-L2884: 'assert not link_dists_2' then 'for spec in order: assert spec in convert_to_dist_str(unlink_dists_2)' over just three records. The port at conda-solver-tests/basic.yaml lines 4050-4079 pins 28 unlink records plus 'link_precs: []', with no solvers restriction, and the description (lines 3996-3999) declares 'the full unlink set here is pinned from solver behaviour'.

### B169

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_mkl::2`

The concrete 14-record final_state is not stated anywhere upstream. Upstream only asserts that the two solves are equal to each other. The port's list is identical to the stage-1 sibling B158's list, so upstream's equality is preserved transitively, and the description discloses this, but the state itself is a stricter, execution-derived assertion.

Evidence: Upstream L283-L285 is only 'assert env.install("mkl") == env.install("mkl 11*", MatchSpec(track_features="mkl"))' with no record list. Port basic.yaml L4931-L4944 lists 14 concrete records, matching B158's final_state at L4208-L4221 exactly.

### B170

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_accelerate::2`

Same materialisation as B169. Upstream asserts only that the plain 'accelerate' install equals the install with the track_features spec, with no record list. The port's concrete 15-record state matches the stage-1 sibling B130 exactly, preserving the equality, and the description discloses the convention.

Evidence: Upstream L289-L291 is only 'assert env.install("accelerate") == env.install("accelerate", MatchSpec(track_features="mkl"))'. Port basic.yaml L4967-L4981 lists 15 concrete records, identical to B130's final_state at L4240-L4254.

### B174

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::3`

Upstream makes no assertion at all about this inner solve, it only feeds its records as specs into invocation 4. The port turns it into a standalone solve entry with an exact expected state. The inferred single-record state is consistent with the data and anchors B175's 'libpng==1.2.50=0' handoff, but the assertion itself is synthesized rather than ported.

Evidence: Upstream line 634: 'env.install("mypackage", *env.install("libpng 1.2.*", as_specs=True))', with the inner call unasserted. basic.yaml lines 5996-5999: 'specs_to_add: "libpng 1.2.*"' with final_state exactly [channel-1/${{ arch }}::libpng-1.2.50-0]. The description honestly labels it 'Inner solve of the not-disrupted regression pair'.

### B175

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::4`

Description wording is muddled. It says the solution must 'not be disrupted by the newer-timestamped hash12 build preferences', but hash12 is itself the newer-timestamped build and is the expected solution of this pair, so nothing here could be disrupted by it. The timestamp-disruption risk upstream guards against actually bites in the 1.5 pair (B177), where hash12's newer timestamp could pull the solver away from hash15. The inputs, expected output, and issue 6271 reference are all correct.

Evidence: basic.yaml lines 6010-6012: 'not be disrupted by the newer-timestamped hash12 build preferences' in an entry whose expected state is ts_mypackage-1.0-hash12_0. Upstream lines 630-632: '# this is testing that previously installed reqs are not disrupted # by newer timestamps', with hash12_0 defined at timestamp=1 (line 611) and hash15_0 at timestamp=0 (line 618).

### B176

Upstream: `conda/testing/solver_helpers.py::SolverTests.test_timestamps_and_deps::5`

Same synthesized assertion as B174, for the inner libpng 1.5.* solve of the second regression pair. Upstream asserts nothing about this invocation, the port asserts an exact one-record state that anchors B177's 'libpng==1.5.13=1' handoff.

Evidence: Upstream line 638: 'env.install("mypackage", *env.install("libpng 1.5.*", as_specs=True))', inner call unasserted. basic.yaml lines 6039-6042: 'specs_to_add: "libpng 1.5.*"' with final_state exactly [channel-1/${{ arch }}::libpng-1.5.13-1].

### B178

Upstream: `tests/core/test_solve.py::test_fast_update_with_update_modifier_not_set::2 (libmamba branch)`

For libmamba upstream asserts only that the two python records appear in the unlink and link sets, while the port pins the complete ordered diff including openssl and xz records upstream never asserts for this solver.

Evidence: Upstream L2286-L2294: 'if context.solver == "libmamba":' asserts add_subdir('channel-4::python-2.7.14-h89e7a4a_22') in unlink_precs and add_subdir('channel-4::python-3.6.4-hc3d631a_1') in link_precs, nothing else. The port (basic.yaml lines 2966-2973) additionally asserts unlink of openssl-1.0.2l-h077ae2c_5 and link of openssl-1.0.2p-h14c3975_0 and xz-5.2.4-h14c3975_4, in fixed order. The description discloses 'the full diff here is pinned from solver behaviour', and both upstream-required python records are present. Inputs and the stage-1 handoff prefix match upstream's order1 exactly.

### I001

Upstream: `tests/core/test_solve.py::test_pinned_1::1 through ::8`

The provenance node_id stage numbers for I001 through I008b are off by one against the Nth-solver-invocation convention used elsewhere in the file. I001 is labelled ::1 but ports the second solver invocation, and so on up to I008a/I008b labelled ::8 for the ninth invocation. The freeze_deps_1 and python2_update ports in the same file number stages by solver invocation, so the pinned_1 numbering is internally inconsistent.

Evidence: Upstream test_pinned_1 (L2356-L2603) contains nine solver invocations, the first being the numpy solve at L2357-L2374. integration.yaml line 5 gives I001 'node_id: tests/core/test_solve.py::test_pinned_1::1' for the system=5.8=0 solve, which is invocation 2 (upstream L2377-L2384). By contrast I010 (line 380) labels the first invocation of test_freeze_deps_1 as ::1.

### I009

Upstream: `tests/cli/test_main_install.py::test_install_freezes_env_by_default`

Upstream only asserts that the packages present before the --freeze-installed install (dependent 1.0 and dependency 1.0) keep their versions afterwards. The port asserts an exact three-record final state, adding another_dependent-2.0-0 and a specific record order that upstream never checks. The extra content is consistent with the upstream recipe data (another_dependent depends only on 'dependent' and 2.0 is its latest version), so this pins solver behaviour rather than contradicting upstream.

Evidence: Upstream tests/cli/test_main_install.py L46-L50: 'for pkg in pkgs: assert prefix_data.get(pkg["name"]).version == pkg["version"]', with no assertion on another_dependent's version or on ordering. integration.yaml I009 lines 372-375 assert final_state '[dependency-1.0-0, dependent-1.0-0, another_dependent-2.0-0]', and the harness asserts exact order (install.py line 292).

### I014

Upstream: `tests/core/test_solve.py::test_freeze_deps_1::5`

Upstream conditionally omits xz-5.2.3-0 from the expected unlink order when running libmamba with libmambapy older than 2.0a0. The port expects xz in unlink_precs unconditionally for both solvers and does not document dropping the branch. This matches upstream for classic and for any current libmambapy 2.x, and deviates only for the obsolete libmamba v1 case, so it cannot flip pass or fail in this repo's environments.

Evidence: Upstream L3164-L3176: unlink_order includes '"channel-2::xz-5.2.3-0"' only when not (context.solver == "libmamba" and VersionOrder(version("libmambapy")) < VersionOrder("2.0a0")), marked '# LIBMAMBA ADJUSTMENT / libmamba v1 doesn't remove xz in this solve'. integration.yaml I014 lines 532-535 list unlink_precs as six-1.7.3-py34_0, python-3.4.5-0, xz-5.2.3-0 with no solvers restriction and no mention of the version branch.

### I015

Upstream: `tests/core/test_solve.py::test_freeze_deps_1::6`

Two description inaccuracies. First, it claims bokeh=0.12.5 'requires python<3.0', but channel-2 also carries py35 and py36 builds of bokeh 0.12.5, so the real reason for the failure is that no build is compatible with the frozen python 3.4. Second, it says the test is 'Same as test_freeze_deps_1_4 but with update_modifier set to freeze_installed', omitting that the operation also differs, solve_final_state here versus solve_for_diff in I013.

Evidence: Upstream index2.json at commit 03329e0f contains bokeh-0.12.5-py35_0/_1 and bokeh-0.12.5-py36_0/_1 with depends 'python 3.5*' and 'python 3.6*' (mirrored in the ported channel-2_non-noarch.json). Upstream L3204-L3213 calls 'solver.solve_final_state(update_modifier=UpdateModifier.FREEZE_INSTALLED)' while stage 4 (L3138-L3146) calls solve_for_diff. integration.yaml I015 description is at lines 564-567.

### C006

Upstream: `tests/core/test_solve.py::test_cuda_glibc_sat`

The description claims cuda-glibc depends on both __cuda and __glibc, but in the upstream channel data __glibc is only a constrains entry, not a dependency.

Evidence: Port cuda.yaml L98-L100: 'A package that depends on both the __cuda and __glibc virtual packages'. Upstream tests/data/index.json cuda-glibc-10.0-0 record: 'depends': ['__cuda>=10.0,<11'], 'constrains': ['__glibc>=2.17'], and the port's channel-1 data matches that.

### S001

Upstream: `tests/core/test_solve.py::test_determine_constricting_specs_conflicts`

The mypkg record's fn was normalised away from upstream's copy-paste quirk. Harmless since determine_constricting_specs never reads fn.

Evidence: Upstream L3506 has fn="mypkg-0.1.1" on the record whose version is "0.1.0". Port constricting_specs.yaml L22 has 'fn: mypkg-0.1.0'.

### S001

Upstream: `tests/core/test_solve.py::test_determine_constricting_specs_conflicts (applies identically to S002-S007)`

All seven ported constricting-specs tests build the solver over channel-1 with the default linux-64 plus noarch subdirs, whereas upstream builds it over the conda_format_repo directory channel with linux-64 only. No behavioural impact because determine_constricting_specs never consults the index, and the solve is never invoked.

Evidence: Upstream L3520-L3522: 'context.plugin_manager.get_solver_backend()(tmpdir, (Channel(CHANNEL_DIR_V1),), ("linux-64",), specs_to_add=[spec])' where CHANNEL_DIR_V1 is tests/data/conda_format_repo. Port constricting_specs.yaml L13 'channels: channel-1' with the models.py L76-L78 default subdirs ('linux-64', 'noarch'), even though a conda_format_repo channel and TestChannel.CONDA_FORMAT_REPO exist in the port.

### WB-test_globstr_matchspec_non_compatible_construction

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible (case 1)`

The port drops upstream's @pytest.mark.integration marker, so the case runs unconditionally in the ported suite while upstream only runs it in integration test runs. Assertion semantics are unchanged.

Evidence: Upstream tests/core/test_solve.py L3832 reads '@pytest.mark.integration' directly above 'def test_globstr_matchspec_non_compatible(tmpdir):' at L3833. The port at /Users/agriyakhetarpal/Desktop/pytest-conda-solvers/pytest_conda_solvers/base_tests/solve.py lines 181-203 defines test_globstr_matchspec_non_compatible_construction with no equivalent marker or gating.

### WB-test_globstr_matchspec_non_compatible_construction

Upstream: `tests/core/test_solve.py::test_globstr_matchspec_non_compatible (cases 2-3)`

The docstring cross-reference says cases 2-3 are ported as B083/B084, but those two ids are the classic-only halves (solvers: classic). The libmamba halves are B083b/B084b, which the docstring omits, so a reader following the reference could conclude libmamba coverage was dropped.

Evidence: solve.py line 191: 'Cases 2-3 are ported as B083/B084 in conda-solver-tests/basic.yaml.' In basic.yaml, B083 (line 4692) and B084 (line 4732) each carry 'solvers: classic' with 'exception: ResolvePackageNotFound', while the libmamba variants B083b (line 4712) and B084b (line 4752) carry 'solvers: libmamba' with 'exception: PackagesNotFoundError'. Together the four cover upstream's pytest.raises((PackagesNotFoundError, ResolvePackageNotFound)) at L3851 and L3857, but the docstring names only two of them.

### WB-test_solve_2_ssc_add_back

Upstream: `tests/core/test_solve.py::test_solve_2 (stage 1 assertion)`

The harness convert_to_dist_str returns an IndexedSet, which cannot hold duplicates, whereas upstream returns a tuple. The stage 1 order assertion is therefore marginally weaker than upstream: a solution containing two records that render to the same dist string would collapse to one entry and pass in the port while failing upstream. The test's central stage 3 dedup assert is unaffected because it iterates final_state directly.

Evidence: Upstream conda/testing/helpers.py L726-L727: 'def convert_to_dist_str(solution): return tuple(prec.dist_str(canonical_name=False) for prec in solution)'. Port install.py lines 87-88: 'return IndexedSet(prec.dist_str() for prec in state)', consumed at solve.py line 65: 'assert list(convert_to_dist_str(final_state)) == list(order)'.

## Coverage statement

Every id below was individually compared against its upstream original at the pinned provenance
commit, and none was unverifiable:


B001, B002, B003, B004, B005, B006, B007, B007b, B008, B009, B010, B011, B012, B013, B014, B015, B016, B017, B018, B019, B020, B021, B022, B023, B024a, B024b, B025, B026, B027, B028, B029, B030, B031, B032, B033, B034, B035, B036, B037, B038, B043, B044, B045, B046, B047, B048, B049, B050, B051, B052, B053, B054, B054b, B055, B056, B056b, B057, B057b, B058, B059, B060, B061, B062, B063, B064, B065, B066, B067, B068, B069, B070, B071, B072, B073, B074, B075, B076, B077, B083, B083b, B084, B084b, B085, B086, B087, B088, B089, B090, B091, B092, B093, B094, B095, B096, B097, B098, B099, B100, B101, B102, B103, B104, B105, B105b, B106, B107, B108, B109, B110, B112, B113, B114, B115, B116, B117, B118, B119, B120, B121, B122, B123, B124, B125, B126, B127, B128, B129, B130, B131, B132, B133, B134, B135a, B135b, B136a, B136b, B137, B138, B139, B140, B141, B142, B143, B144, B145a, B145b, B146a, B146b, B147, B148, B149, B150, B151, B152, B153, B154, B155, B156, B157, B158, B159, B160, B161, B162, B163, B164, B165, B166, B167, B168, B169, B170, B171, B172, B173, B174, B175, B176, B177, B178, I001, I002, I003, I004, I004b, I005, I006, I007, I008a, I008b, I009, I010, I011, I012, I013, I014, I015, I016, I017, I017b, C001, C002, C003, C004, C005, C006, C007, S001, S002, S003, S004, S005, S006, S007, WB-test_force_reinstall_1_sequence, WB-test_globstr_matchspec_non_compatible_construction, WB-test_solve_2_ssc_add_back
