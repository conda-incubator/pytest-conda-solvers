from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

import msgspec
import pytest
from conda.core.solve import Solver
from conda.core.subdir_data import SubdirData
from conda.models.match_spec import MatchSpec
from conda.models.records import PackageRecord
from conda.models.records import PrefixRecord as CondaPrefixRecord

from pytest_conda_solvers.base_tests.install import (
    TestBasic as _TestBasic,
    add_base_url,
    get_solver,
    prepare_error_information,
)
from pytest_conda_solvers.models import (
    DeterminingConstrictingSpecsTestOutput,
    PackagesNotFoundTestError,
    PrefixRecord,
    ResolvePackageNotFoundTestError,
    SpecsConfigurationConflictTestError,
    TestInput as _TestInput,
    TestModule as _TestModule,
    UnsatisfiableTestError,
)
from pytest_conda_solvers.paths import solver_tests_path


@pytest.mark.parametrize("custom_first", [False, True])
def test_get_solver_refreshes_custom_multichannel_records(
    tmpdir, channel_server, custom_first
):
    channel_url = channel_server.get_channel_url("channel-4")
    SubdirData._cache_.clear()
    try:
        for custom in (custom_first, not custom_first):
            with get_solver(
                Solver,
                tmpdir.mkdir(f"prefix-{custom}"),
                channel_server,
                ["custom"] if custom else ["channel-4"],
                ("linux-64", "noarch"),
                specs_to_add=[MatchSpec("anaconda-docs")],
                custom_multichannels={"custom": ["channel-4"]} if custom else None,
            ) as solver:
                channel = "custom" if custom else channel_url
                assert [record.dist_str() for record in solver.solve_final_state()] == [
                    f"{channel}/noarch::anaconda-docs-2.0.27-0"
                ]
    finally:
        SubdirData._cache_.clear()


@pytest.mark.parametrize(
    ("dist_strs", "expected"),
    [
        (None, ()),
        (
            "channel-1/${{ arch }}::numpy-1.0-0",
            ("https://example.test/channel-1/linux-64::numpy-1.0-0",),
        ),
        (
            [
                "channel-1/${{ arch }}::numpy-1.0-0",
                "channel-1/noarch::pip-1.0-0",
            ],
            (
                "https://example.test/channel-1/linux-64::numpy-1.0-0",
                "https://example.test/channel-1/noarch::pip-1.0-0",
            ),
        ),
    ],
)
def test_add_base_url_accepts_model_values(dist_strs, expected):
    assert add_base_url("https://example.test", "linux-64", dist_strs) == expected


@pytest.mark.parametrize(
    "error",
    [
        UnsatisfiableTestError(entries="numpy"),
        ResolvePackageNotFoundTestError(entries="numpy"),
        PackagesNotFoundTestError(entries="numpy"),
    ],
)
def test_prepare_error_information_preserves_scalar_entry(error):
    error_info = prepare_error_information(error, "classic")

    assert error_info["entries"] == {(MatchSpec("numpy"),)}


@pytest.mark.parametrize("field", ["requested_specs", "pinned_specs"])
def test_specs_configuration_conflict_rejects_nested_specs(field):
    data = {
        "exception": "SpecsConfigurationConflictError",
        "requested_specs": "numpy",
        "pinned_specs": "python",
    }
    data[field] = [["numpy"]]

    with pytest.raises(msgspec.ValidationError, match=rf"\$\.{field}\[0\]"):
        msgspec.convert(data, type=SpecsConfigurationConflictTestError)


@pytest.mark.parametrize(
    ("solution_records", "expected_names"),
    [
        (None, []),
        (
            PrefixRecord(
                name="numpy",
                version="1.0",
                channel="test",
                subdir="linux-64",
                fn="numpy-1.0-0.tar.bz2",
            ),
            ["numpy"],
        ),
    ],
)
def test_determine_constricting_specs_accepts_model_values(
    solution_records, expected_names
):
    test = SimpleNamespace(
        input=_TestInput(specs_to_add="numpy", solution_records=solution_records),
        output=DeterminingConstrictingSpecsTestOutput(constrictions=None),
    )
    solver = Mock()
    solver.determine_constricting_specs.return_value = None
    setup = nullcontext(
        (
            solver,
            {"specs_to_add": (MatchSpec("numpy"),)},
            {},
            {},
        )
    )
    runner = _TestBasic()

    with patch.object(runner, "_setup_solver", return_value=setup):
        runner.test_determine_constricting_specs(None, None, None, test, None)

    _, solution_records = solver.determine_constricting_specs.call_args.args
    assert all(isinstance(record, CondaPrefixRecord) for record in solution_records)
    assert [record.name for record in solution_records] == expected_names


@pytest.mark.parametrize("solver_name", ["classic", "libmamba", "rattler"])
@pytest.mark.parametrize(
    ("unlink_sqlite", "sqlite_version", "python_version", "valid"),
    [
        (True, "3.23.0", None, True),
        (True, "3.24.0", "2.7.15", True),
        (False, "3.24.0", None, False),
        (True, None, None, False),
        (True, "3.21.0", None, False),
        (True, "3.9.0", None, False),
        (True, "3.24.0", "3.6.6", False),
    ],
)
def test_fast_update_diff_checks(
    solver_name, unlink_sqlite, sqlite_version, python_version, valid
):
    module = msgspec.yaml.decode(
        (solver_tests_path() / "basic.yaml").read_bytes(), type=_TestModule
    )
    test = next(test for test in module.tests if test.id == "B071")

    def record(name, version):
        return PackageRecord(
            name=name,
            version=version,
            build="0",
            build_number=0,
            channel="https://example.test/channel-4",
            subdir="linux-64",
        )

    old_sqlite = record("sqlite", "3.21.0")
    unlink = [old_sqlite] if unlink_sqlite else []
    link = [record("sqlite", sqlite_version)] if sqlite_version else []
    if python_version:
        link.append(record("python", python_version))
    solver = Mock()
    solver.solve_for_diff.return_value = unlink, link
    setup = nullcontext((solver, {"prefix_records": [old_sqlite]}, {}, {}))
    request = SimpleNamespace(
        config=SimpleNamespace(option=SimpleNamespace(conda_solver=solver_name))
    )
    channel_server = Mock()
    channel_server.get_base_url.return_value = "https://example.test"
    runner = _TestBasic()
    # Classic still requires all five package changes from B071's exact diff.
    expected = (
        nullcontext()
        if valid and solver_name != "classic"
        else pytest.raises(AssertionError)
    )
    with patch.object(runner, "_setup_solver", return_value=setup), expected:
        runner.test_fast_update_diff(request, None, None, None, test, channel_server)
