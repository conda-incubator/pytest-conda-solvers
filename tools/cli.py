from enum import Enum
from pathlib import Path

import msgspec
import msgspec.structs
import msgspec.yaml
import typer
from conda.core.solve import UpdateModifier

from pytest_conda_solvers.models import (
    ChannelPriority,
    DeterminingConstrictingSpecsTestOutput,
    Provenance,
    TestChannel,
    TestInput,
    TestModule,
    UnsatisfiableTestError,
)

app = typer.Typer(help="CLI tool for pytest-conda-solvers")

# Directory containing the real, CI-validated YAML test fixtures. Example
# generation pulls real entries from here by ``id`` so that the generated
# docs examples stay tied to actual (already schema-checked) test data
# instead of hand-copied or fully synthetic content.
FIXTURES_DIR = Path("pytest_conda_solvers/conda-solver-tests")

# The fixture IDs used to build the generated documentation examples. If any
# of these are ever renamed or removed from the fixtures, ``generate_examples``
# must fail loudly rather than silently producing stale/placeholder output.
FIXTURE_IDS = ("B001", "B005", "B007", "B034", "S001", "I004")


@app.command()
def generate_schemas(
    output: Path | None = None,
    compact: bool = False,
    check: bool = False,
):
    """Generate the JSON schema for ``TestModule``.

    With ``--check``, nothing is written. Instead, the freshly generated
    schema is compared against the current contents of ``--output`` and the
    command exits non-zero if they differ (or if ``--output`` doesn't exist
    yet), printing instructions for regenerating the file. This is used by
    the ``check-cst-schema`` pre-commit hook to catch a stale
    ``docs/cst_schema.json`` before it gets committed.
    """
    schema = msgspec.json.schema(TestModule)
    compact_representation = msgspec.json.encode(schema).decode("utf-8")
    representation = (
        compact_representation
        if compact
        else msgspec.json.format(compact_representation)
    )
    # Files written to disk get a trailing newline so they satisfy the
    # `end-of-file-fixer` pre-commit hook; stdout output is left as-is
    # since `print` already appends its own newline.
    file_representation = (
        representation if representation.endswith("\n") else representation + "\n"
    )
    if check:
        if output is None:
            raise typer.BadParameter("--check requires --output to be set")
        current = output.read_text() if output.exists() else None
        if current != file_representation:
            typer.echo(
                f"{output} is out of date with the schema generated from "
                "pytest_conda_solvers/models.py.\n"
                "Run `pixi run generate-schema` (or `pixi run -e docs "
                "docs-schema`) and commit the result.",
                err=True,
            )
            raise typer.Exit(1)
        return
    if output is None:
        print(representation)
    else:
        output.write_text(file_representation)


def _load_fixture_specs(fixtures_dir: Path) -> dict[str, object]:
    """Load every real test spec from the YAML fixtures, keyed by ``id``."""
    specs: dict[str, object] = {}
    for path in sorted(fixtures_dir.glob("*.yaml")):
        module = msgspec.yaml.decode(path.read_bytes(), type=TestModule)
        for spec in module.tests:
            specs[spec.id] = spec
    return specs


def _prune_defaults(value, keep: frozenset[str] = frozenset()):
    """Recursively convert a msgspec ``Struct`` (or nested value) into plain
    builtins suitable for YAML encoding, omitting any field whose value
    equals that field's declared default (unless the field's name is in
    ``keep``). This mirrors how the real hand-written fixture files already
    look: they simply don't mention optional fields they don't use.

    Discriminator/tag fields (e.g. ``kind``, ``exception``, ``record_type``)
    are always included, since they're required for the data to be
    decodable back into the correct type.
    """
    if isinstance(value, msgspec.Struct):
        cls = type(value)
        config = cls.__struct_config__
        result = {}
        if config.tag_field is not None:
            result[config.tag_field] = config.tag
        for field in msgspec.structs.fields(cls):
            field_value = getattr(value, field.name)
            if field.name not in keep:
                if (
                    field.default is not msgspec.NODEFAULT
                    and field_value == field.default
                ):
                    continue
                if (
                    field.default_factory is not msgspec.NODEFAULT
                    and field_value == field.default_factory()
                ):
                    continue
            result[field.encode_name] = _prune_defaults(field_value)
        return result
    elif isinstance(value, (list, tuple)):
        return [_prune_defaults(item) for item in value]
    elif isinstance(value, dict):
        return {key: _prune_defaults(item) for key, item in value.items()}
    elif isinstance(value, Enum):
        return value.value
    else:
        return value


def _emit(
    output_dir: Path,
    filename: str,
    value,
    type_: type,
    *,
    keep: frozenset[str] = frozenset(),
) -> None:
    """Prune defaults, encode as YAML, round-trip validate against ``type_``,
    and write to ``output_dir / filename``. Raises if the round trip fails,
    so that a broken/stale example fails the docs build instead of silently
    shipping invalid documentation.
    """
    pruned = _prune_defaults(value, keep=keep)
    buf = msgspec.yaml.encode(pruned)
    msgspec.yaml.decode(buf, type=type_)  # round-trip validation
    (output_dir / filename).write_bytes(buf)


@app.command()
def generate_examples(output_dir: Path | None = None):
    """Generate the YAML example files used by ``docs/test-schema.rst``.

    The large, narrative test-spec examples are pulled directly from the
    real fixtures in ``conda-solver-tests/`` by ``id``, so they stay in sync
    with the actual test corpus (which is already schema-validated on every
    test run). The smaller field-shape snippets are built from
    constructed/reused model instances and validated by round-tripping
    through ``msgspec.yaml.decode``.
    """
    if output_dir is None:
        output_dir = Path("docs/examples")
    output_dir.mkdir(parents=True, exist_ok=True)

    fixture_specs = _load_fixture_specs(FIXTURES_DIR)
    missing = [id_ for id_ in FIXTURE_IDS if id_ not in fixture_specs]
    if missing:
        raise ValueError(
            f"Expected fixture ids not found in {FIXTURES_DIR}: {missing}. "
            "The generated documentation examples reference these ids "
            "directly -- if they were renamed or removed, update "
            "FIXTURE_IDS and the examples in generate_examples() to match."
        )

    b001, b005, b007, b034, s001, i004 = (fixture_specs[id_] for id_ in FIXTURE_IDS)

    # -- Full test-spec examples (real fixtures) -----------------------
    _emit(output_dir, "test_module.yaml", TestModule(tests=[b001, b005]), TestModule)
    _emit(output_dir, "solve.yaml", b001, type(b001))
    _emit(output_dir, "solve_for_diff.yaml", b034, type(b034))
    _emit(
        output_dir,
        "determine_constricting_specs.yaml",
        s001,
        type(s001),
    )
    _emit(
        output_dir,
        "unsatisfiable_unsatisfiable_error.yaml",
        b005,
        type(b005),
    )
    _emit(
        output_dir,
        "unsatisfiable_resolve_package_not_found.yaml",
        b007,
        type(b007),
    )
    _emit(
        output_dir,
        "unsatisfiable_specs_configuration_conflict.yaml",
        i004,
        type(i004),
    )

    # -- Field-shape snippets (real fixtures where possible) ------------
    _emit(output_dir, "input_minimal.yaml", b001.input, TestInput)

    input_complete = TestInput(
        channels=[TestChannel.CHANNEL_4, TestChannel.CHANNEL_2],
        specs_to_add=["flask"],
        history_specs=["flask==0.12"],
        prefix=[
            "channel-4/${{ arch }}::python-3.6.6-hc3d631a_0",
            "channel-2/${{ arch }}::flask-0.12-py36_0",
        ],
        pinned_packages=["python=3.6"],
        update_modifier=UpdateModifier.UPDATE_SPECS,
        channel_priority=ChannelPriority.FLEXIBLE,
    )
    _emit(output_dir, "input_complete.yaml", input_complete, TestInput)

    prefix_record = s001.input.solution_records[1]
    _emit(output_dir, "prefix_record.yaml", prefix_record, type(prefix_record))

    _emit(output_dir, "test_output.yaml", b001.output, type(b001.output))
    _emit(output_dir, "diff_test_output.yaml", b034.output, type(b034.output))

    _emit(
        output_dir,
        "constricting_specs_output_empty.yaml",
        DeterminingConstrictingSpecsTestOutput(constrictions=None),
        DeterminingConstrictingSpecsTestOutput,
        keep=frozenset({"constrictions"}),
    )
    _emit(
        output_dir,
        "constricting_specs_output.yaml",
        s001.output,
        type(s001.output),
    )

    _emit(output_dir, "error_unsatisfiable.yaml", b005.error, type(b005.error))
    _emit(
        output_dir,
        "error_unsatisfiable_empty.yaml",
        UnsatisfiableTestError(entries=[]),
        UnsatisfiableTestError,
    )
    _emit(
        output_dir,
        "error_resolve_package_not_found.yaml",
        b007.error,
        type(b007.error),
    )
    _emit(
        output_dir,
        "error_specs_configuration_conflict.yaml",
        i004.error,
        type(i004.error),
    )

    _emit(output_dir, "provenance.yaml", b001.provenance, Provenance)


if __name__ == "__main__":
    app()
