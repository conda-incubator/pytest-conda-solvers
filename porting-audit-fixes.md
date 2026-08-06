# Porting audit fixes, 2026-08-06

Companion to porting-audit.md. Twelve fixer agents worked through all 131 tests that carried
audit findings or failed under the corrected harness, each in an isolated worktree, verifying
every fix by running both solvers explicitly. The harness corrections landed first as local
edits: the order assertion now really enforces order (it silently degraded to a set comparison
before), the declared exception type on unsatisfiable tests is now enforced, a must-solve mode
covers tests where upstream only requires that the solve succeeds, and the deliberate libmamba
error-message strengthening is documented in the README.

Policies applied, as agreed: parity for inputs, applicability, and error expectations, must-solve
conversions where upstream asserts nothing (B135, B136, B139, with their a/b splits merged back),
keep-and-disclose where the port asserts more than upstream, and per-solver splits where the two
solvers genuinely diverge.

Dispositions: 91 fixed, 39 documented (description or
provenance text only), 1 wontfix, 0 needing
a decision. Nothing was committed: all changes are working-tree edits awaiting review, tagged
with the stack branch each belongs to.

New entries created by the fixes: B062b, B063b, B064b, B067b, B068b, B128b, B179, I000, C003b, C004b.

## Final verification

With every fix applied and the corrected harness enforcing record order and declared exception
types, the full suite passes on both solvers:

- classic: 202 passed, 22 skipped
- libmamba: 168 passed, 51 skipped, 5 xfailed (strict)

For comparison, the corrected harness against the unfixed tests failed 40 tests on classic and
24 on libmamba, so every one of those latent divergences is now resolved rather than masked.

## Per-test dispositions

### B001 (fixed, PR stack/01)

The unordered-comparison weakness is a harness defect resolved by the separately-landing harness patch. With order enforcement active, solve_1_1 passes on both solvers and its pinned order already matches upstream's asserted tuple, so no YAML change was needed.

### B002 (documented, PR stack/01)

Ran the entry on libmamba twice with the fixed harness: it passes deterministically (python-2.7.5-0, not the 2.6.8 divergence upstream's flaky marker tolerates), so per policy it stays unrestricted and strict. Added a description note naming upstream's flaky(reruns=5) marker with a permalink.

### B003 (fixed, PR stack/01)

Restricted to solvers: classic because upstream's tests_to_skip excludes test_iopro_mkl on libmamba (features unsupported), with a description permalink. Also pinned the final_state in the classic solver's true order, disclosed as a strengthening since upstream asserts an unordered set.

### B004 (fixed, PR stack/01)

Added add_pip: true to match the upstream fixture's index (get_index_r_1 defaults add_pip=True), pinned the 107-record final_state in the observed solver order (identical on classic and libmamba), and added a description disclosing that upstream asserts only len == 107 plus one scipy membership.

### B005 (fixed, PR stack/01)

Both findings are resolved by the separately landing harness patch: the declared exception type is now enforced with an isinstance assertion, and the libmamba endpoint-name strengthening is deliberately kept and disclosed in the README per maintainer policy. No YAML change needed, and the test is green on both solvers with the patch applied.

### B007b (documented, PR stack/01)

Added a description disclosure that upstream checks nothing beyond the exception for the PackagesNotFoundError case and that the harness compares package names only, so the version text in entries is informative rather than asserted. The entries text is kept since removing it would weaken an existing check.

### B008 (fixed, PR stack/01)

Added aggressive_update_packages: "" so the harness sets CONDA_AGGRESSIVE_UPDATE_PACKAGES to an empty string, matching upstream's monkeypatch.setenv("CONDA_AGGRESSIVE_UPDATE_PACKAGES", ""), instead of leaving conda's default aggressive list active. Behaviour unchanged, test passes on both solvers. B010 and B013 need the same fix but were not in my item list, see notes.

### B014 (fixed, PR stack/01)

The unordered-comparison weakness is the same harness defect fixed by the separately-landing harness patch. test_aggressive_update_packages_7 passes on both solvers with order enforcement active, so no YAML change was needed.

### B019 (documented, PR stack/01)

Ran on libmamba twice with the fixed harness: passes deterministically, so per the non-strict-xfail policy the entry stays unrestricted and strict. Added a description note naming upstream's known-flaky xfail on libmamba with a permalink.

### B020 (documented, PR stack/01)

Same as B019: deterministic pass on libmamba across two runs, entry left unrestricted, description note added naming upstream's non-strict known-flaky xfail with a permalink.

### B021 (documented, PR stack/01)

Same as B019 and B020: deterministic pass on libmamba across two runs, entry left unrestricted, description note added naming upstream's non-strict known-flaky xfail with a permalink.

### B022 (fixed, PR stack/01)

Ported the dropped libmamba branch of test_conda_downgrade stage 4 as a new entry test_conda_downgrade_4b (B179, solvers: libmamba), pinning the observed deterministic libmamba diff, which I verified satisfies upstream's four version-property checks (conda 4.3.30 < 4.4.10, python 3.6.2, conda-build 3.12.1, itsdangerous 0.24). Added a description to B022 explaining the classic restriction and pointing at B179.

### B023 (fixed, PR stack/01)

Converted to must-solve per policy: dropped the synthesised 43-record final_state (upstream only pprints this solve without asserting), set output: {}, and added a description saying upstream asserts success only, with the permalink. Passes on both solvers in must-solve mode.

### B024a (documented, PR stack/01)

Kept the pinned exact unlink and link records per policy and added a description line disclosing that upstream asserts only len(unlink) == 1 and len(link) == 1, with the permalink.

### B024b (documented, PR stack/01)

Rewrote the description to disclose upstream's length-only assertions with permalinks, credit the force_reinstall input to upstream's libmamba-only solver kwargs, and mark the same-build-reinstall claim as an observation of this port rather than an upstream fact. Pinned records unchanged.

### B025 (documented, PR stack/01)

Added a description note disclosing that upstream gives classic system[version=*,build_number=0] and libmamba system[version=*,build=*0], while the port uses the libmamba form for both solvers. Both forms match the same single channel-1 package, so behaviour is unchanged.

### B026 (documented, PR stack/01)

Added the same disclosure for the history_specs carrying the libmamba form of the system spec for both solvers, with the upstream permalink.

### B027 (documented, PR stack/01)

Added the disclosure of the solver-conditional system spec form, plus the explanation that UPDATE_ALL reduces history specs to names, which is why system-5.8-1 legitimately appears despite the build-0 constraint.

### B032 (fixed, PR stack/01)

Reordered final_state to upstream's asserted stage-5 order with unixodbc-2.3.1-0 first. Both solvers produce exactly that order here, matching upstream at the pinned commit, and both pass under the new order-strict harness. The harness weakening in the second finding is resolved by the separately-landing harness patch.

### B045 (fixed, PR stack/01)

The finding is about the harness's ineffective ordering assertion, which the separately-landing harness patch fixes (list-vs-list comparison). No YAML change needed: B045 passes order-strict on both solvers with the patch applied, so the pinned order is the true solver order.

### B046 (documented, PR stack/01)

Corrected the factually wrong description claim that numba=0.5 requires numpy>=1.7. Channel-1 ships np16 and np17 builds needing numpy 1.6* or 1.7*, neither satisfiable by the history-pinned numpy=1.5. The exception-type finding is resolved by the harness patch, and entries: [] matches upstream's bare pytest.raises(UnsatisfiableError).

### B050 (fixed, PR stack/05)

The order-insensitivity the audit found is in the shared runner and is resolved by the separately-landing harness patch (list-vs-list comparison now enforces order). No YAML change needed: with the patched harness B050 passes on both solvers, so its pinned 7-record link order is the true solver order.

### B052 (fixed, PR stack/07)

Ported upstream's classic conflict-chain entries [(numpy=1.5,), (scipy==0.12.0b1, numpy 1.6.*|1.7.*)] into the YAML, matching the formatting of the sibling B005 port. The exception-type laxity finding is addressed by the separately landing harness patch, and the add_pip note was left as is since the audit itself concludes it has no effect on the asserted outcome and it is a family-wide convention.

### B053 (fixed, PR stack/07)

Ported upstream's three classic conflict chains [(numpy=1.5, nose, python=3.3), (numpy=1.5, python 2.6.*|2.7.*), (python=3,)] into the YAML, matching the sibling B006 port's formatting.

### B054b (documented, PR stack/07)

Kept the package-name entry check per the do-not-weaken policy and added a description line disclosing that upstream asserts nothing on the PackagesNotFoundError branch, so the name check is a deliberate strengthening.

### B055 (fixed, PR stack/07)

Order-only ground-truth failure under the new order assertion. Reordered final_state to the order both solvers actually produce. Upstream asserts a set at L847-L860, so there is no upstream order to conflict with.

### B056 (fixed, PR stack/07)

Restored input parity by adding a new channel-empty (empty repodata for both subdirs, plus a TestChannel enum entry) and pointing the test at it instead of the populated channel-1, so the failure is a missing package in an empty index as upstream has it.

### B056b (fixed, PR stack/07)

Same empty-channel fix as B056 for the libmamba variant, now solving against channel-empty. Passes with PackagesNotFoundError as declared.

### B057 (fixed, PR stack/07)

Switched to channel-empty and rewrote the description: the failure is now the numpy name missing entirely, as upstream has it, rather than a missing exact version among channel-1's numpy 1.5.1 builds.

### B057b (fixed, PR stack/07)

Same empty-channel fix and description correction as B057 for the libmamba variant.

### B058 (fixed, PR stack/07)

Ported upstream's conflict chains [(a, c>=1,<2), (b, c>=2,<3)] with channel-7's us_ renaming, and noted the renaming in the description. Both solvers pass, classic against the exact chain set and libmamba against endpoint names in the message.

### B059 (fixed, PR stack/07)

Ported upstream's conflict chains [(a, b, c>=1,<2), (e, c>=2,<3)] with channel-7's uc_ renaming, and noted the renaming in the description. Both solvers pass.

### B060 (fixed, PR stack/07)

Ported upstream's two conflict chains for test_unsat_expand_single into entries, replacing entries: []. Classic now asserts the exact chain set and libmamba the endpoint names, and both pass.

### B061 (fixed, PR stack/07)

Ported upstream's chains [(um_a, um_b), (um_b,)] into entries, replacing entries: []. Both solvers pass.

### B062 (fixed, PR stack/07)

Ported upstream's four chains. libmamba's message omits sc1_b (its unconstrained sc1_c dep is not part of libmamba's minimal conflict explanation), and upstream's chain assertion is gated on the exact UnsatisfiableError type so it only runs for classic, so the entry was split into B062 (classic, full chains) and B062b (libmamba, chains minus the sc1_b chain) per the existing a/b convention.

### B063 (fixed, PR stack/07)

Ported upstream's four chains. Same libmamba message gap as B062 (sc2_b never named), so split into B063 (classic, full chains) and B063b (libmamba, chains minus the sc2_b chain).

### B064 (fixed, PR stack/07)

Ported upstream's three chains. Same libmamba message gap as B062 (sc3_b never named), so split into B064 (classic, full chains) and B064b (libmamba, chains minus the sc3_b chain).

### B065 (fixed, PR stack/07)

Ported upstream's chains [(sc4_a, sc4_py=3.7.1), (sc4_py=3.6.1,)] into entries, replacing entries: []. Both solvers pass, no split needed.

### B067 (fixed, PR stack/04)

Split into B067a (classic) and B067b (libmamba) per the existing a/b convention, each carrying upstream's per-solver error-message snippets as message_includes. Upstream's two libmamba regex snippets are realised as literal fragments verified against the actual message, disclosed in the description.

### B068 (fixed, PR stack/04)

Split into B068a (classic) and B068b (libmamba), each carrying upstream's per-solver error-message snippets as message_includes. The libmamba regex snippet python.*2.6 is realised as the literal fragment python=2.6 verified against the actual message, disclosed in the description.

### B071 (documented, PR stack/03)

Added a description line disclosing that upstream asserts the full ordered diff for classic only, while for libmamba it checks only that sqlite is upgraded past 3.21 and any linked python stays at 2.7, with the permalink. Per policy the strengthened full-diff assertion is kept, and both solvers were verified to produce this exact diff.

### B073 (fixed, PR stack/07)

Made the input faithful to upstream's repo (index_packages(1) plus the circular pair) by adding channel-1 alongside channel-7 and add_pip: true, matching the B101-B103 convention for the same upstream construct, with a description note and permalink. Outcome unchanged, verified on both solvers.

### B083 (documented, PR stack/06)

Declared exception type is now enforced by the harness patch (entry stays green under classic). The audit's claim that upstream stage ::1 is unported is wrong at the stack tip: commit 7385cda on stack/06-feature-tests ports it as the white-box test test_globstr_matchspec_non_compatible_construction in pytest_conda_solvers/base_tests/solve.py. Added a description note cross-referencing that port.

### B083b (documented, PR stack/06)

Same as B083 for the libmamba variant: type enforcement comes from the harness patch (green under libmamba), and the description now cross-references the white-box ValueError port of upstream stage ::1.

### B084 (fixed, PR stack/06)

The unenforced declared exception type is fixed by the separately-landing harness patch, which now asserts isinstance against the YAML-declared class. No YAML change needed: classic raises ResolvePackageNotFound as declared, verified green with enforcement active.

### B084b (fixed, PR stack/06)

Same as B084 for the libmamba variant: harness patch enforces the declared PackagesNotFoundError, verified green under libmamba with enforcement active.

### B085 (documented, PR stack/07)

Kept the pinned full ordered state per policy and added a description line disclosing that upstream asserts only membership of a-1.0 and b-1.0, with the permalink to L542-L544.

### B086 (documented, PR stack/07)

Kept the pinned full ordered state and added a disclosure line that upstream asserts only membership of a-2.0 and c-1.0, with the permalink to L546-L548.

### B087 (documented, PR stack/07)

Kept the pinned full ordered state and added a disclosure line that upstream asserts only membership of b-2.0 and c-2.0, with the permalink to L550-L552.

### B088 (fixed, PR stack/07)

Ported upstream's three atnt_d version-range chains into entries, replacing entries: []. Both solvers pass, no split needed.

### B091 (documented, PR stack/07)

Corrected the factually wrong claim that the dep exists in both subdirs (upstream's package2 is arch-only, and channel-7 matches), and disclosed that upstream asserts only the pulled-in package's noarch subdir, with permalink.

### B092 (documented, PR stack/07)

Disclosed in the description that the channel data names the noarch build string '1' where upstream keeps '0' with build_number 1 (behaviourally neutral, the discriminator is the build number), and that upstream asserts only one record from noarch. Changing the shared channel-7 data would also affect B093, so disclosure was chosen over a data edit.

### B093 (documented, PR stack/07)

Corrected the wrong claim that the dep is arch-preferred with equal versions in both subdirs (it exists only in the arch subdir, matching upstream), and disclosed the strengthening over upstream's subdir-only assertion, with permalink.

### B094 (fixed, PR stack/06)

Added solvers: classic because upstream skips test_no_features entirely for libmamba (tests_to_skip, permalink added to the description), and reordered final_state to the true classic solver order now that order is enforced. Upstream asserts full set equality, so the content is unchanged.

### B095 (fixed, PR stack/07)

Added solvers: classic because upstream's TestLibMambaSolver.tests_to_skip lists test_pseudo_boolean (features unsupported), matching sibling B171, with the permalink in the description. Also reordered final_state to the true classic solver order, fixing the order-assertion failure.

### B101 (fixed, PR stack/07)

Order-only ground-truth failure. Reordered final_state to the order both solvers produce. Upstream asserts a set, so no conflict.

### B102 (fixed, PR stack/07)

Order-only ground-truth failure. Reordered final_state to the shared solver order, with nd_anotherpackage-1.0 last. Upstream asserts a set.

### B103 (fixed, PR stack/07)

Order-only ground-truth failure. Reordered final_state to the shared solver order, with nd_anotherpackage-2.0 last. Upstream asserts a set.

### B104 (fixed, PR stack/07)

Reordered final_state to the true solver order, which is identical on classic and libmamba. Upstream compares against an unordered set literal, so there is no upstream order to diverge from.

### B105 (documented, PR stack/07)

The type-enforcement gap is closed by the separately landing harness patch, and ResolvePackageNotFound (classic) is admitted by upstream's pytest.raises tuple, so no YAML behaviour change is needed. Added a description line disclosing that pinning the exact type per solver is stricter than upstream's two-type tuple, with the permalink. Upstream asserts no chains at this stage, so entries: [] stays faithful.

### B105b (documented, PR stack/07)

Corrected the TODO permalink from L752-L754 to L751-L754 so it covers the full upstream comment. The type-enforcement gap is closed by the harness patch, and UnsatisfiableError (libmamba) is admitted by upstream's pytest.raises tuple.

### B106 (fixed, PR stack/07)

Reordered final_state to the true solver order, identical on both solvers, with nd2_anotherpackage-1.0-0 last. Upstream asserts an unordered set.

### B107 (fixed, PR stack/07)

Reordered final_state to the true solver order, identical on both solvers, with nd2_anotherpackage-2.0-0 last. Upstream asserts an unordered set.

### B108 (documented, PR stack/07)

Added a description line disclosing that upstream asserts only membership of the two records and that the exact full state is a deliberate strengthening, with the permalink to lines 623-625. Assertions unchanged per policy.

### B109 (documented, PR stack/07)

Same disclosure as B108 for the libpng 1.5.* stage, with the permalink to lines 627-629. Assertions unchanged.

### B110 (fixed, PR stack/07)

Corrected the provenance node_id stage suffix from ::3 to ::7, matching the seventh env.install invocation (line 643) and freeing ::3 for B174, which genuinely ports the inner libpng 1.2.* solve.

### B113 (fixed, PR stack/02)

Upstream carries an active strict xfail for libmamba, so the port's solvers: classic (a skip) was replaced with xfail_solvers: libmamba plus xfail_reason, with a permalink note in the description. Verified: classic passes and libmamba strict-xfails, rerun once to confirm stability.

### B117 (fixed, PR stack/03)

Upstream never reaches this stage under libmamba because the function-level strict xfail fails at the stage-1 order assertion first, so the strict xfail here risked an XPASS with no upstream expectation behind it. Replaced xfail_solvers with solvers: classic and a description note mirroring the sibling B115, with the permalink to the applymarker block.

### B124 (fixed, PR stack/02)

Upstream stage 1 computes final_state_1 without asserting anything about it, matching the must-solve pattern, so the invented 51-record final_state was dropped (output: {}) and the description now says upstream asserts success only, with the permalink. Verified passing on both solvers in must-solve mode.

### B125 (documented, PR stack/02)

Upstream asserts only three conditional attribute checks, weaker than a full state, so per policy the pinned full state is kept and one description line now discloses the strengthening with the permalink to L3811-L3817. Verified still green on both solvers.

### B128 (fixed, PR stack/05)

With order enforced, libmamba returns the same record set with numpy last while classic matches upstream's numpy-first asserted tuple (test_solve.py L914-L925). Split per the a/b convention: B128 is now solvers: classic keeping upstream's order, and a new B128b (test_force_remove_1_3b, following the I017/I017b naming precedent) pins the libmamba order, with descriptions noting that upstream never observes the libmamba order because the whole function carries a strict libmamba xfail (L857-L864).

### B129 (fixed, PR stack/05)

The order weakness is resolved by the harness patch and classic passes with upstream's exact tuple order enforced. Also corrected the now factually wrong description claim that stages 1-3 pass under libmamba: stage 3 differs in order (see B128b), and this stage's libmamba failure is on content (python is not restored), which I confirmed with --runxfail, so the strict xfail_solvers: libmamba stays.

### B130 (fixed, PR stack/06)

Added the ::1 stage suffix to node_id (matching sibling B158's style), added a description line disclosing that upstream only asserts equality of the two solves so the pinned full state is a strengthening, and reordered final_state to the true classic order.

### B131 (fixed, PR stack/06)

Ground-truth failure with no finding: reordered final_state to the true classic solver order now that the harness enforces order. Set unchanged, description already discloses the strengthening.

### B132 (fixed, PR stack/06)

Reordered the 51-record final_state to the true solver order, which classic and libmamba produce identically (verified empirically), so one list serves both and no a/b split is needed. Added a description line disclosing that upstream asserts only membership of two records.

### B133 (fixed, PR stack/06)

Converted solvers: classic to xfail_solvers: libmamba with upstream's strict-xfail reason, and reordered final_state to upstream's asserted tuple order, which matches the observed classic order exactly. Libmamba xfails deterministically (ran twice).

### B134 (fixed, PR stack/06)

Reordered final_state to upstream's asserted tuple order (matches observed classic order exactly). The audit's xfail_solvers recommendation was tried and rejected empirically: this stage XPASSes under libmamba here, because upstream's function-level strict xfail fails at stage 1 so stage 2 is never reached under libmamba. Applied the unreachable-stage mapping instead: solvers: classic with an explanatory permalinked description.

### B135a (fixed, PR stack/06)

Merged the a/b pair into one must-solve entry B135 keeping the base name: dropped the invented 13-record final_state (output: {}), removed the solvers restriction, and the description now says upstream asserts success only, with the permalink. Passes on both solvers.

### B135b (fixed, PR stack/06)

Deleted: its libmamba-specific invented state is absorbed by the merged must-solve entry B135, which passes on both solvers.

### B136a (fixed, PR stack/06)

Merged the a/b pair into one must-solve entry B136 keeping the base name: dropped the invented 22-record final_state, removed the solvers restriction, description discloses upstream asserts success only with the permalink. Passes on both solvers.

### B136b (fixed, PR stack/06)

Deleted: absorbed by the merged must-solve entry B136, which passes on both solvers.

### B137 (documented, PR stack/06)

Rewrote the description: the higher package2 version (2.0 over 1.0, both build 0) wins, not a higher build, and package1 is a feature carrier via features while the feature package provides it via track_features. No input or assertion changes.

### B138 (documented, PR stack/06)

Rewrote the description to state that upstream's two package2 1.0 records collide on filename in the written repodata, so only the build_number 1 record survives and no build-number competition is exercised, with the upstream permalink. channel-9 already mirrors the surviving record, so no data or assertion changes.

### B139 (fixed, PR stack/06)

Converted to must-solve per policy: dropped the invented 11-record final_state (output: {}), removed the wrong 'Features are classic-only.' claim (upstream runs this under libmamba too), and the description now says upstream asserts success only, with the permalink to the '# should not raise' comment. Passes on both solvers.

### B140 (fixed, PR stack/06)

Reordered the pinned final_state into true classic solver order (ground-truth order failure) and added a description line disclosing that upstream asserts only the two scipy membership facts (permalink L826-L827), that the full list is pinned from classic behaviour, and that the bad scipy record lives permanently in shared channel-1 while upstream serves it only within this test.

### B143 (fixed, PR stack/02)

The finding is resolved by the separately-landing harness patch, which now asserts isinstance against the declared exception type. Upstream asserts only pytest.raises(UnsatisfiableError) with no chain content, so entries: [] is faithful and no YAML change is needed. Verified green on both solvers with the patched harness (libmamba raises LibMambaUnsatisfiableError, a subclass, which upstream's pytest.raises admits).

### B145a (fixed, PR stack/03)

Upstream stage 1 asserts nothing about the solution (its only extra assertion is a stdout absence check that is vacuous on an empty prefix and not representable here), and the a/b split carried identical inputs, so per the must-solve policy B145a and B145b were merged into a single unrestricted must-solve entry B145 (name test_update_prune_5_1) with the disclosure and permalink in the description. Verified passing on both solvers.

### B145b (fixed, PR stack/03)

Deleted as part of the merge into must-solve B145, since the split existed only to carry invented per-solver states over identical inputs. Its former pinned libmamba state survives only as B146b's handoff prefix, which is an input and matches upstream's per-solver stage-1 handoff.

### B146a (fixed, PR stack/03)

Reordered the pinned final_state into the true classic solver order (verified empirically, upstream asserts no order or state for this stage) and added a description line stating the final state is pinned from solver behaviour. Verified passing on classic, skipped on libmamba as before.

### B146b (fixed, PR stack/03)

Reordered the pinned final_state into the true libmamba solver order and added the missing disclosure that upstream asserts only the stdout diagnostic absence (which classic alone prints) and never the solution, so the state is pinned from solver behaviour. Verified passing on libmamba.

### B147 (fixed, PR stack/03)

Reordered the pinned final_state into the true classic order and added the pinned-from-behaviour disclosure. The policy mapping of upstream's active strict xfail to xfail_solvers was tried and empirically rejected: libmamba XPASSes (strict) because it reproduces the exact classic final state, and upstream's libmamba failure lives solely in the unrepresentable stdout assertion. Following the verify-empirically rule, the entry is left unrestricted (run twice on libmamba, deterministic pass) with the upstream xfail and its scope disclosed in the description.

### B148 (wontfix, PR stack/04)

No change needed: the finding itself records that the description already discloses both the upstream non-strict xfail and the impossible stage-1 assertion (a record absent from upstream's channel-A), which is exactly what the policy requires. The entry passes on both solvers with the fixed harness.

### B149 (documented, PR stack/04)

Added a description line disclosing that upstream never enforces this assertion because the whole method is a non-strict xfail, with the permalink to the xfail marker.

### B150 (documented, PR stack/04)

Added the same non-strict xfail disclosure line with permalink as B149, which the audit noted was missing from this entry.

### B151 (fixed, PR stack/04)

Ground-truth order failure with no finding: the expected final_state was not in true solver order. Both classic and libmamba produce c-2.0, a-1.0, b-1.0, so the list was reordered. Upstream asserts membership only (under a non-strict xfail, already disclosed), so there is no upstream order to conflict with. Stable across two runs on each solver.

### B152 (fixed, PR stack/04)

Reordered the expected final_state to the true solver order (c-2.0, a-2.0, b-2.0, identical on both solvers) and added the missing description disclosure that upstream is a non-strict xfail whose first classic assertion fails at this stage, so the outcome was never verified upstream. Stable across two runs on each solver.

### B153 (documented, PR stack/04)

Description now discloses the input substitution: upstream literally sets CONDA_CHANNEL_PRIORITY=True (flexible, the same setting under which its stage 1 succeeds), and strict is used here to realise the intended unsatisfiability. The extra a-c chain stays because classic genuinely reports it (exact set equality would fail without it) and it was already disclosed, and the libmamba endpoint-name check is the deliberate harness strengthening documented in the README.

### B154 (fixed, PR stack/05)

Reordered the final state from alphabetical to the true classic solver order (upstream compares this state as an unordered set at solver_helpers.py L1057-L1108, so there is no upstream order to preserve), and added the description note the audit asked for: upstream's non-strict class-level xfail about global state (L1053-L1056), which asserts nothing, with the stage passing deterministically here (verified over three classic runs).

### B155 (fixed, PR stack/05)

Same treatment as B154: final state reordered to the observed classic order, upstream set-comparison and non-strict xfail disclosed in the description with permalinks. Passed deterministically over three classic runs.

### B156 (fixed, PR stack/05)

Same treatment as B154: final state reordered to the observed classic order, upstream set-comparison and non-strict xfail disclosed in the description with permalinks. Passed deterministically over three classic runs.

### B158 (fixed, PR stack/06)

Added the ::1 stage suffix to the node_id, reordered the final_state into true classic solver order, and added a description line disclosing that upstream asserts only equality with the test_mkl_2 solve, with the permalink. The observed order is identical to B169's, so upstream's equality is preserved.

### B161 (fixed, PR stack/05)

Reordered the pinned 28-record unlink list from alphabetical to the true solver unlink order, which I verified is identical for classic and libmamba, and extended the existing disclosure sentence to say the order is also pinned from solver behaviour and shared by both solvers. Upstream asserts only three-record containment plus empty link set, so no upstream order exists to cross-check.

### B163 (fixed, PR stack/04)

Ground-truth order failure with no finding: the expected final_state was alphabetically sorted, not in solver order. Repinned to the observed classic order (the only applicable solver, upstream strict-xfails libmamba with run=False). Upstream asserts only membership of the channel-4 python and pandas records, both present, and that strengthening was already disclosed.

### B164 (fixed, PR stack/04)

Same alphabetical-order ground-truth failure as B163, repinned to the observed classic order. The channel-2 portion matches the package order upstream asserts for the equivalent stage-1 state, supporting fidelity. Upstream asserts only the two channel-2 records, already disclosed.

### B165 (fixed, PR stack/05)

Reordered the pinned final state from alphabetical to the true classic solver order (ca-certificates first, then the channel-2 stack in dependency order). Upstream asserts only python and six membership plus pandas absence (test_solve.py L2981-L2989), already disclosed in the description, so only the order needed pinning.

### B166 (fixed, PR stack/06)

Ground-truth order failure with no finding: reordered the final_state into true classic solver order (mkl-rt first, then the dependency-ordered stack). Upstream asserts a set, so there is no upstream order to diverge from.

### B167 (fixed, PR stack/06)

Ground-truth order failure with no finding: reordered the final_state into true classic solver order. Upstream asserts a set, so there is no upstream order to diverge from.

### B168 (fixed, PR stack/06)

Ground-truth order failure with no finding: reordered the final_state into true classic solver order. Upstream asserts a set, so there is no upstream order to diverge from.

### B169 (fixed, PR stack/06)

Reordered the final_state into true classic solver order, identical to B158's observed order, preserving upstream's equality assertion, and tightened the description to say the state is pinned from classic solver behaviour.

### B170 (fixed, PR stack/06)

Reordered the final_state into true classic solver order (B158's order plus accelerate last, matching the observed solve), and tightened the description to say the state is pinned from classic solver behaviour. The set still equals B130's, preserving upstream's equality.

### B171 (fixed, PR stack/07)

Reordered final_state to the true classic solver order (the entry is classic-only and stays so). Upstream asserts an unordered set, so the reorder is the only change needed.

### B172 (fixed, PR stack/07)

Added channel-1 alongside channel-7 to restore upstream's input (index_packages(1) plus the two synthetic records). Outcome unchanged, both solvers still produce exactly package1 then package2.

### B173 (fixed, PR stack/07)

Same channel-1 addition as B172 for the package2 stage. Verified on both solvers with the outcome unchanged.

### B174 (documented, PR stack/07)

Added a disclosure that upstream makes no direct assertion on this inner solve and only feeds its records into the next invocation, with the permalink. The pinned one-record state is kept because it anchors B175's libpng==1.2.50=0 handoff and removing it would weaken an existing, empirically true assertion. The must-solve conversion pattern (per-solver splits carrying invented states) does not apply here.

### B175 (documented, PR stack/07)

Rewrote the muddled description: the newer-timestamped hash12 build is itself the expected pick in this pair, so the timestamp disruption upstream guards against can only bite in the 1.5 pair. Tightened the permalink to lines 630-636. Inputs and expected output were already correct.

### B176 (documented, PR stack/07)

Same disclosure as B174 for the inner libpng 1.5.* solve, naming the libpng==1.5.13=1 handoff in test_timestamps_and_deps_7, with the permalink to lines 637-640.

### B178 (fixed, PR stack/03)

Fixed the link_precs order to the true libmamba order (openssl, xz, python), observed empirically. Upstream asserts only python membership for libmamba, which the pinned diff satisfies, and the description already discloses the pinning from solver behaviour. Verified passing on libmamba, skipped on classic as intended.

### I001 (fixed, PR stack/01)

Ported the missing first invocation of test_pinned_1 (the numpy solve before pins are set) as new entry I000 (pinned_1_0), verified passing and order-stable twice per solver, and corrected the off-by-one node_id stage suffixes on I001 through I008b to the Nth-invocation convention (::2 through ::9).

### I009 (documented, PR stack/01)

Added a description line disclosing that upstream only asserts dependent and dependency keep version 1.0, so the exact three-record final state and its order are a strengthening, with the upstream permalink. Entry verified green on both solvers under order enforcement.

### I013 (fixed, PR stack/01)

Resolved by the harness patch's exception-type enforcement, which lands separately. Upstream stage 4 asserts only pytest.raises(UnsatisfiableError) around solve_for_diff with no content check, so entries: [] and operation: solve_for_diff are exact parity. Green on both solvers with the patch applied.

### I014 (documented, PR stack/01)

Added a description line disclosing the dropped libmamba-v1 branch in which upstream omits xz-5.2.3-0 from the unlink order for libmambapy older than 2.0a0, obsolete for the versions tested here.

### I015 (documented, PR stack/01)

Rewrote the description to fix both inaccuracies: it now says the stage calls solve_final_state with freeze_installed where stage 4 calls solve_for_diff, and attributes the failure to channel-2 having no bokeh=0.12.5 build for the frozen python 3.4 (only py27, py35, and py36 builds exist) rather than the false claim that bokeh 0.12.5 requires python<3.0.

### I017b (fixed, PR stack/08)

Reordered the pinned 31-record final state from alphabetical to the true libmamba topological order. The strengthening over upstream's three-package subset check (test_solve.py L2026-L2046) is already disclosed in the description, and the pinned state still contains upstream's three required records plus the cryptography-2.3/cryptography-vectors difference.

### C003 (fixed, PR stack/01)

Ported upstream's solver-specific message assertions by splitting into a classic variant (C003, message_includes covering the full upstream message except the platform-dependent feature line) and a new libmamba variant (C003b, pinning upstream's first accepted problem message). Chains via entries were impossible because classic's UnsatisfiableError.unsatisfiable is only populated for the direct class, not virtual_package errors.

### C004 (fixed, PR stack/01)

Same treatment as C003: classic variant C004 now asserts the complete upstream message via three fragments including 'Your installed version is: not available', and new libmamba variant C004b pins upstream's first accepted problem message with a disclosure that upstream accepts either of two.

### C006 (documented, PR stack/01)

Corrected the factually wrong claim that cuda-glibc depends on __glibc (it is a constrains entry) and disclosed upstream's Linux-only skipif with the permalink, noting the override is inert on non-Linux hosts while the test still passes there. The harness has no platform-restriction mechanism, so disclosure is the available remedy.

### S001 (fixed, PR stack/01)

Disclosed the strengthening from upstream's name-membership assert to the exact list, restored upstream's fn copy-paste quirk (mypkg-0.1.1 on the 0.1.0 record) with a description note, and switched the input to upstream's conda_format_repo channel with linux-64 subdirs for parity (applied to S004-S007 too per this finding's parenthetical). All seven tests pass on both solvers.

### S002 (fixed, PR stack/01)

Disclosed the strengthening to the exact single-element list with the upstream permalink and applied the conda_format_repo/linux-64 input parity switch. Passes on both solvers.

### S003 (fixed, PR stack/01)

Disclosed that both the exact two-element list and its mypkgnot-before-notmypkg order strengthen upstream's two membership asserts, with the permalink, and applied the input parity switch. Passes on both solvers.

### WB-test_globstr_matchspec_non_compatible_construction (documented, PR stack/06)

Docstring-only fix: disclosed that upstream gates the test behind @pytest.mark.integration while it runs unconditionally here, and corrected the cross-reference to name all four ported halves B083/B084 (classic) and B083b/B084b (libmamba). Assertion code untouched.

### WB-test_solve_2_ssc_add_back (fixed, PR stack/02)

Replaced the IndexedSet-based stage-1 order assertion with a direct duplicate-preserving list comprehension so two records rendering to the same dist string can no longer collapse and pass, matching upstream's tuple semantics, and removed the now-unused convert_to_dist_str import. Verified passing on classic (skips on libmamba by design).
