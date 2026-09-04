# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from enum import Enum
from typing import Literal, TypeAlias

from conda.core.solve import UpdateModifier, DepsModifier
from conda.models.enums import PackageType
from conda.models.match_spec import MatchSpec
from msgspec import Struct, field


class TestChannel(Enum):
    """Enumeration of test channel identifiers available in the test fixture data.

    These names correspond to the channel directories bundled with the test suite.
    """

    CHANNEL_1 = "channel-1"
    CHANNEL_2 = "channel-2"
    CHANNEL_4 = "channel-4"
    CHANNEL_6 = "channel-6"
    CHANNEL_7 = "channel-7"
    CHANNEL_8 = "channel-8"
    CHANNEL_9 = "channel-9"
    CHANNEL_10 = "channel-10"
    CHANNEL_11 = "channel-11"
    CHANNEL_12 = "channel-12"
    CHANNEL_13 = "channel-13"
    CHANNEL_14 = "channel-14"
    CHANNEL_FREEZE = "channel-freeze"
    CONDA_FORMAT_REPO = "conda_format_repo"
    TEST = "test"

    def __str__(self):
        return self.value


class TestSubdir(Enum):
    """Enumeration of platform subdirectories available in the test fixture data."""

    NOARCH = "noarch"
    LINUX_64 = "linux-64"
    CONDA_TEST = "conda-test"

    def __str__(self):
        return self.value


class ChannelPriority(Enum):
    """Enumeration of channel priority modes, mirroring conda's ``ChannelPriority`` setting.

    Controls whether packages from higher-priority channels are preferred over
    those from lower-priority channels when both satisfy a requirement.
    """

    STRICT = "strict"
    FLEXIBLE = "flexible"
    DISABLED = "disabled"

    def __str__(self):
        return self.value


class PrefixRecord(
    Struct,
    tag_field="record_type",
    tag="prefix",
    frozen=True,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Represents a package record in the solution inspected by
    ``determine_constricting_specs()``. The ``record_type`` discriminator field
    is always ``"prefix"`` and is set automatically.
    """

    package_type: PackageType | None = None
    """The conda package type. Optional; defaults to ``None``.
    Valid values mirror ``conda.models.enums.PackageType``, e.g.
    ``"noarch_generic"``, ``"noarch_python"``, ``"virtual_system"``, etc."""

    name: str
    """The package name (e.g. ``"numpy"``)."""

    version: str
    """The package version string (e.g. ``"1.24.3"``)."""

    channel: str
    """The channel the package was installed from (e.g. ``"conda-forge"``)."""

    subdir: str
    """The platform subdirectory the package belongs to (e.g. ``"linux-64"``)."""

    fn: str
    """The filename of the package archive
    (e.g. ``"numpy-1.24.3-py311h0000000_0.conda"``)."""

    build: str = "0"
    """The build string (e.g. ``"py311h0000000_0"``). Defaults to ``"0"``."""

    build_number: int = 0
    """The build number. Defaults to ``0``."""

    paths_data: list[str] | None = None
    """List of relative paths recorded in the package's path data. Optional."""

    files: list[str] | None = None
    """List of files installed by the package. Optional."""

    depends: list[str] = []
    """List of run-dependency match specs (e.g. ``["python >=3.11", "numpy"]``).
    Defaults to an empty list."""

    constrains: list[str] = []
    """List of match specs describing optional runtime constraints (`run_constrained`)."""


class TestInput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """Describes the solver inputs for a single test case.

    Most fields are optional. Each field's description explains how ``None``
    is handled.
    """

    channels: TestChannel | list[TestChannel] | None = None
    """The channel(s) to make available to the solver. May be a single
    :class:`TestChannel` value or a list of them. ``None`` means no test
    channels are supplied."""

    subdirs: TestSubdir | list[TestSubdir] = field(
        default_factory=lambda: ["linux-64", "noarch"]
    )
    """The platform subdirectory (or list of subdirectories) to consider
    when resolving packages. Defaults to ``["linux-64", "noarch"]``."""

    specs_to_add: str | list[str] | None = None
    """The package spec(s) to add/install in this solve. May be a single
    match-spec string or a list. ``None`` means no new specs are added."""

    specs_to_remove: str | list[str] | None = None
    """The package spec(s) to remove in this solve. May be a single
    match-spec string or a list. ``None`` means nothing is removed."""

    prefix: str | list[str] | None = None
    """Installed package distribution string(s) used to populate the temporary
    prefix before solving. May be a single string or a list. ``None`` means the
    prefix starts empty."""

    history_specs: str | list[str] | None = None
    """Match spec(s) representing the history of explicitly requested packages
    in the prefix. May be a single string or a list. ``None`` means no
    history is set."""

    solution_records: PrefixRecord | list[PrefixRecord] | None = None
    """Package record(s) in the candidate solution inspected by
    ``determine_constricting_specs()``. May be a single :class:`PrefixRecord` or
    a list. ``None`` means no solution records are supplied."""

    add_pip: bool = False
    """Whether to add ``pip`` as an implicit dependency. Defaults to ``False``."""

    ignore_pinned: bool | None = None
    """Whether to ignore pinned package constraints during the solve.
    ``None`` means use the solver default."""

    force_reinstall: bool | None = None
    """Whether to force reinstallation of already-satisfied packages.
    ``None`` means use the solver default."""

    prune: bool | None = None
    """Whether to remove packages that are no longer needed by any
    history spec. ``None`` means use the solver default."""

    force_remove: bool | None = None
    """Whether to remove the requested packages without removing their
    dependents. ``None`` means use the solver default."""

    pinned_packages: str | list[str] | None = None
    """Package spec(s) to pin (hold at their current version). May be a
    single string or a list. ``None`` means no packages are pinned."""

    aggressive_update_packages: str | list[str] | None = None
    """Package spec(s) that should be aggressively updated when possible.
    May be a single string or a list. ``None`` means use the solver default."""

    auto_update_conda: bool | None = None
    """Whether conda itself should be auto-updated during the solve.
    ``None`` means use the solver default."""

    update_modifier: UpdateModifier | None = None
    """Controls how already-installed packages are treated during an update.
    ``None`` means use the solver default. Valid string values mirror
    ``conda.core.solve.UpdateModifier``: ``"freeze_installed"``,
    ``"specs_satisfied_skip_solve"``, ``"update_all"``, ``"update_deps"``,
    ``"update_specs"``."""

    deps_modifier: DepsModifier | None = None
    """Controls whether dependencies are installed, skipped, or exclusively
    targeted. ``None`` means use the solver default. Valid string values
    mirror ``conda.core.solve.DepsModifier``: ``"no_deps"``,
    ``"not_set"``, ``"only_deps"``."""

    channel_priority: ChannelPriority | None = None
    """The channel priority mode to use for this solve. ``None`` means use
    the solver default. See :class:`ChannelPriority` for valid values."""

    set_sys_prefix: bool | None = None
    """Whether to set ``sys.prefix`` as the target prefix. ``False`` or
    ``None`` leaves ``sys.prefix`` unchanged."""

    override_cuda: str | None = None
    """Override the detected CUDA version string (e.g. ``"11.8"``).
    ``None`` means no override; the solver uses its auto-detected value."""

    override_glibc: str | None = None
    """Override the detected glibc version string (e.g. ``"2.17"``).
    ``None`` means no override; the solver uses its auto-detected value."""


class TestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected output for a ``kind: solve`` test case.

    Describes the expected final state returned by a successful solve.
    """

    final_state: str | list[str] | None = None
    """The expected package distribution string(s) returned by the solve.
    ``None`` only asserts that the solve succeeds without checking its result."""


class DiffTestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected output for a ``kind: solve_for_diff`` test case.

    Describes the expected package-level diff (unlinks and links) produced by
    the solver rather than the full final environment state.
    """

    unlink_precs: str | list[str] | None = None
    """The package distribution string(s) expected to be unlinked from the
    prefix. ``None`` means no unlinks are expected."""

    link_precs: str | list[str] | None = None
    """The package distribution string(s) expected to be linked into the
    prefix. ``None`` means no links are expected."""


class UnsatisfiableTestError(
    Struct,
    tag_field="exception",
    tag="UnsatisfiableError",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected error for a test where the solver should raise ``UnsatisfiableError``.

    The ``exception`` discriminator field is always ``"UnsatisfiableError"``
    and is set automatically.
    """

    entries: str | list[str | list[str]]
    """The conflicting dependency chain(s) that make the environment
    unsatisfiable. Each entry may be a single string or a list of strings
    representing one conflict path. May also be given as a single string
    instead of a list when there is only one entry."""

    # message fragments may be either a single string, a list that applies to
    # every solver, or a mapping keyed by solver name. A mapping needs a key for
    # each solver the entry runs on. Use an empty value for a solver with
    # nothing to check. A missing key is an error.
    message_excludes: str | list[str] | dict[str, str | list[str]] = []
    """Substring(s) that must NOT appear in the raised exception's message.
    May be a single string, a list, or a mapping keyed by solver name.
    Defaults to an empty list (no exclusion checks)."""

    message_includes: str | list[str] | dict[str, str | list[str]] = []
    """Substring(s) that must appear in the raised exception's message.
    May be a single string, a list, or a mapping keyed by solver name.
    Defaults to an empty list (no inclusion checks)."""


class PackagesNotFoundTestError(
    Struct,
    tag_field="exception",
    tag="PackagesNotFoundError",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected error for a test where the solver should raise ``PackagesNotFoundError``.

    The ``exception`` discriminator field is always ``"PackagesNotFoundError"``
    and is set automatically.
    """

    entries: str | list[str | list[str]]
    """The package spec(s) that could not be found in any configured channel.
    Each entry is a string or list of strings. May also be given as a
    single string instead of a list when there is only one entry."""


class ResolvePackageNotFoundTestError(
    Struct,
    tag_field="exception",
    tag="ResolvePackageNotFound",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected error for a test where the solver should raise ``ResolvePackageNotFound``.

    The ``exception`` discriminator field is always ``"ResolvePackageNotFound"``
    and is set automatically.
    """

    entries: str | list[str | list[str]]
    """The package spec(s) that could not be resolved. Each entry is a string
    (or list of strings) describing the missing package. May also be given
    as a single string instead of a list when there is only one entry."""


class SpecsConfigurationConflictTestError(
    Struct,
    tag_field="exception",
    tag="SpecsConfigurationConflictError",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected error for a test where the solver should raise ``SpecsConfigurationConflictError``.

    This error occurs when explicitly requested specs conflict with pinned
    package constraints. The ``exception`` discriminator field is always
    ``"SpecsConfigurationConflictError"`` and is set automatically.
    """

    requested_specs: str | list[str]
    """The explicitly requested spec(s) that conflict with pinned constraints.
    May be a single string or a list of strings."""

    pinned_specs: str | list[str]
    """The pinned spec(s) that conflict with the requested specs. May be a
    single string or a list of strings."""


TestError: TypeAlias = (
    UnsatisfiableTestError
    | ResolvePackageNotFoundTestError
    | PackagesNotFoundTestError
    | SpecsConfigurationConflictTestError
)


class Provenance(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """Records the origin of a test case — where it came from in the conda source tree.

    This information is used to trace each test back to its upstream source
    commit and to generate links to the original test in the conda repository.
    """

    node_id: str
    """The pytest node ID of the original test in the upstream conda test suite
    (e.g. ``"tests/test_solve.py::TestSolveUserStories::test_install_numpy"``)."""

    commit: str
    """The full Git commit SHA of the upstream conda commit the test was
    ported from (e.g. ``"03329e0f4a627c9b9aa92ef34f7f93b9aa83e438"``)."""

    url: str
    """The URL to the specific source file in the upstream conda repository at
    the recorded commit, linking directly to the test's location on GitHub."""


class SolveTestSpec(
    Struct,
    tag_field="kind",
    tag="solve",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Test spec for a standard solve operation (``kind: solve``).

    Asserts that the solver produces a specific final environment state
    given the inputs. The ``kind`` discriminator field is always ``"solve"``
    and is set automatically.
    """

    name: str
    """A human-readable name for the test (e.g. ``"test_install_numpy"``)."""

    id: str
    """A stable unique identifier for this test case. Used to look up the
    test by ID independently of its name or position in the file."""

    provenance: Provenance
    """Provenance information linking this test back to its upstream source."""

    input: TestInput
    """The solver inputs for this test case."""

    output: TestOutput
    """The expected output (final environment state) after the solve."""

    description: str | None = None
    """An optional human-readable description of what this test exercises.
    Defaults to ``None``."""

    test_function: str = "test_solve"
    """The name of the base-test method to invoke for this spec.
    Defaults to ``"test_solve"``."""

    solvers: str | list[str] | None = None
    """Restrict this test to a specific solver backend or list of backends
    (e.g. ``"classic"`` or ``["classic", "libmamba"]``). ``None`` means
    the test runs against all registered solver backends."""

    xfail_solvers: str | list[str] | None = None
    """Solver backend(s) for which this test is expected to fail (xfail) rather
    than error. May be a single string or a list. ``None`` means no solver is
    expected to fail."""

    xfail_reason: str | None = None
    """A human-readable explanation of why the solver(s) in ``xfail_solvers``
    are expected to fail. ``None`` if not applicable."""


class SolveForDiffTestSpec(
    Struct,
    tag_field="kind",
    tag="solve_for_diff",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Test spec for a solve-for-diff operation (``kind: solve_for_diff``).

    Asserts that the solver produces specific unlink/link package sets rather
    than a full final environment state. The ``kind`` discriminator field is
    always ``"solve_for_diff"`` and is set automatically.
    """

    name: str
    """A human-readable name for the test."""

    id: str
    """A stable unique identifier for this test case."""

    provenance: Provenance
    """Provenance information linking this test back to its upstream source."""

    input: TestInput
    """The solver inputs for this test case."""

    output: DiffTestOutput
    """The expected diff output (packages to unlink and link)."""

    description: str | None = None
    """An optional human-readable description of what this test exercises.
    Defaults to ``None``."""

    test_function: str = "test_solve_for_diff"
    """The name of the base-test method to invoke for this spec.
    Defaults to ``"test_solve_for_diff"``."""

    solvers: str | list[str] | None = None
    """Restrict this test to a specific solver backend or list of backends.
    ``None`` means the test runs against all registered solver backends."""

    xfail_solvers: str | list[str] | None = None
    """Solver backend(s) for which this test is expected to fail (xfail) rather
    than error. May be a single string or a list. ``None`` means no solver is
    expected to fail."""

    xfail_reason: str | None = None
    """A human-readable explanation of why the solver(s) in ``xfail_solvers``
    are expected to fail. ``None`` if not applicable."""


class Constriction(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """A single constricting package relationship identified by the solver.

    Represents one entry in the output of a ``determine_constricting_specs``
    solve, describing which installed package is blocking a requested upgrade
    or installation.
    """

    package: str
    """The name of the installed package that is imposing the constriction
    (e.g. ``"scipy"``)."""

    constricting_match_spec: str
    """The match spec from ``package``'s dependencies that is blocking the
    requested operation (e.g. ``"numpy >=1.22,<1.24"``)."""


class DeterminingConstrictingSpecsTestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    """Expected output for a ``kind: determine_constricting_specs`` test case.

    Describes the set of constricting package relationships the solver is
    expected to identify.
    """

    constrictions: list[Constriction] | None = None
    """The list of constrictions the solver is expected to report. Each entry
    is a :class:`Constriction` describing one blocking dependency. ``None``
    means the solver is expected to report no constrictions."""

    def constrictions_as_list(self):
        return (
            None
            if self.constrictions is None
            else [
                (c.package, MatchSpec(c.constricting_match_spec))
                for c in self.constrictions
            ]
        )


class DetermineConstrictingSpecsTestSpec(
    Struct,
    tag_field="kind",
    tag="determine_constricting_specs",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Test spec for a constricting-specs determination (``kind: determine_constricting_specs``).

    Asserts that the solver correctly identifies which installed packages are
    blocking a requested operation. The ``kind`` discriminator field is always
    ``"determine_constricting_specs"`` and is set automatically.
    """

    name: str
    """A human-readable name for the test."""

    id: str
    """A stable unique identifier for this test case."""

    provenance: Provenance
    """Provenance information linking this test back to its upstream source."""

    input: TestInput
    """The solver inputs for this test case."""

    output: DeterminingConstrictingSpecsTestOutput
    """The expected output listing the constricting package relationships."""

    description: str | None = None
    """An optional human-readable description of what this test exercises.
    Defaults to ``None``."""

    test_function: str = "test_determine_constricting_specs"
    """The name of the base-test method to invoke for this spec.
    Defaults to ``"test_determine_constricting_specs"``."""

    solvers: str | list[str] | None = None
    """Restrict this test to a specific solver backend or list of backends.
    ``None`` means the test runs against all registered solver backends."""

    xfail_solvers: str | list[str] | None = None
    """Solver backend(s) for which this test is expected to fail (xfail) rather
    than error. May be a single string or a list. ``None`` means no solver is
    expected to fail."""

    xfail_reason: str | None = None
    """A human-readable explanation of why the solver(s) in ``xfail_solvers``
    are expected to fail. ``None`` if not applicable."""


class UnsatisfiableTestSpec(
    Struct,
    tag_field="kind",
    tag="unsatisfiable",
    frozen=True,
    forbid_unknown_fields=True,
):
    """Test spec for a solve that is expected to fail (``kind: unsatisfiable``).

    Asserts that the solver raises a specific exception given the inputs.
    The ``kind`` discriminator field is always ``"unsatisfiable"`` and is
    set automatically.
    """

    name: str
    """A human-readable name for the test."""

    id: str
    """A stable unique identifier for this test case."""

    provenance: Provenance
    """Provenance information linking this test back to its upstream source."""

    input: TestInput
    """The solver inputs for this test case."""

    error: TestError
    """The expected error the solver should raise. Must be one of
    :class:`UnsatisfiableTestError`,
    :class:`ResolvePackageNotFoundTestError`,
    :class:`PackagesNotFoundTestError`, or
    :class:`SpecsConfigurationConflictTestError`, discriminated by the
    ``exception`` field."""

    description: str | None = None
    """An optional human-readable description of what this test exercises.
    Defaults to ``None``."""

    operation: Literal["solve_final_state", "solve_for_diff"] = "solve_final_state"
    """Which solve operation is expected to raise the error: computing the
    final environment state or computing the unlink/link diff. Defaults to
    ``"solve_final_state"``."""

    test_function: str = "test_unsatisfiable"
    """The name of the base-test method to invoke for this spec.
    Defaults to ``"test_unsatisfiable"``."""

    solvers: str | list[str] | None = None
    """Restrict this test to a specific solver backend or list of backends.
    ``None`` means the test runs against all registered solver backends."""

    xfail_solvers: str | list[str] | None = None
    """Solver backend(s) for which this test is expected to fail (xfail) rather
    than error. May be a single string or a list. ``None`` means no solver is
    expected to fail."""

    xfail_reason: str | None = None
    """A human-readable explanation of why the solver(s) in ``xfail_solvers``
    are expected to fail. ``None`` if not applicable."""


TestSpec: TypeAlias = (
    SolveTestSpec
    | SolveForDiffTestSpec
    | DetermineConstrictingSpecsTestSpec
    | UnsatisfiableTestSpec
)


class TestModule(Struct):
    """The top-level container for a conda solver test file.

    A test file (typically a ``.yaml`` file) deserializes into a
    ``TestModule``, which holds an ordered list of test specs. Each spec
    is one of the four supported test kinds, discriminated by the ``kind``
    field.
    """

    tests: list[TestSpec]
    """The list of test specs contained in this module. Each element is one
    of :class:`SolveTestSpec`, :class:`SolveForDiffTestSpec`,
    :class:`DetermineConstrictingSpecsTestSpec`, or
    :class:`UnsatisfiableTestSpec`, selected by the ``kind`` field."""
