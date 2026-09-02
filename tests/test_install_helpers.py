from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

import msgspec
import pytest
from conda.models.match_spec import MatchSpec
from conda.models.records import PrefixRecord as CondaPrefixRecord

from pytest_conda_solvers.base_tests.install import (
    TestBasic as _TestBasic,
    add_base_url,
    prepare_error_information,
)
from pytest_conda_solvers.models import (
    DeterminingConstrictingSpecsTestOutput,
    PackagesNotFoundTestError,
    PrefixRecord,
    ResolvePackageNotFoundTestError,
    SpecsConfigurationConflictTestError,
    TestInput as _TestInput,
    UnsatisfiableTestError,
)


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
    error_info = prepare_error_information(error)

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
