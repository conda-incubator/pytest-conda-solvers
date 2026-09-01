.. SPDX-License-Identifier: BSD-3-Clause

JSON Schema for Conda Solver Tests
====================================

This page documents the schema for the declarative YAML test files consumed
by pytest-conda-solvers. Each test file deserialises into a
:class:`~pytest_conda_solvers.models.TestModule` containing an ordered list
of test specs. Four test kinds are supported, each represented by a distinct
class and selected via the ``kind`` discriminator field.

.. note::

   Every YAML example on this page is generated from real
   `conda-solver-tests <https://github.com/conda-incubator/pytest-conda-solvers/tree/main/conda-solver-tests>`_.

Top-level container
--------------------

.. autoclass:: pytest_conda_solvers.models.TestModule
   :members:
   :undoc-members:

A test file consists of a single top-level ``tests`` key whose value is a
list of test specs:

.. literalinclude:: examples/test_module.yaml
   :language: yaml


Test specs
----------

Each element of :attr:`~pytest_conda_solvers.models.TestModule.tests` is one
of the four spec types below, identified by its ``kind`` field.

.. autoclass:: pytest_conda_solvers.models.SolveTestSpec
   :members:
   :undoc-members:

A ``solve`` test asserts that the solver reaches a specific final environment
state. Example (B001):

.. literalinclude:: examples/solve.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.SolveForDiffTestSpec
   :members:
   :undoc-members:

A ``solve_for_diff`` test asserts the set of packages unlinked and linked
rather than the complete final environment state. Example (B034):

.. literalinclude:: examples/solve_for_diff.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.DetermineConstrictingSpecsTestSpec
   :members:
   :undoc-members:

A ``determine_constricting_specs`` test asserts which installed packages are
blocking a requested installation or upgrade. Example (S001):

.. literalinclude:: examples/determine_constricting_specs.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.UnsatisfiableTestSpec
   :members:
   :undoc-members:

An ``unsatisfiable`` test asserts that the solver raises a specific error.
The ``error`` field is a discriminated union — see the `Errors`_ section for
all three error types. Example with ``UnsatisfiableError`` (B005):

.. literalinclude:: examples/unsatisfiable_unsatisfiable_error.yaml
   :language: yaml

Example with ``ResolvePackageNotFound`` (B007):

.. literalinclude:: examples/unsatisfiable_resolve_package_not_found.yaml
   :language: yaml

Example with ``SpecsConfigurationConflictError`` (I004):

.. literalinclude:: examples/unsatisfiable_specs_configuration_conflict.yaml
   :language: yaml


Input
-----

.. autoclass:: pytest_conda_solvers.models.TestInput
   :members:
   :undoc-members:

Most fields are optional. A minimal input only needs ``specs_to_add``:

.. literalinclude:: examples/input_minimal.yaml
   :language: yaml

A more complete input showing prefix pre-population and solver modifiers:

.. literalinclude:: examples/input_complete.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.PrefixRecord
   :members:
   :undoc-members:

Each entry in ``solution_records`` or ``prefix`` that uses the full record
form (as opposed to a ``channel::name-version-build`` string) looks like:

.. literalinclude:: examples/prefix_record.yaml
   :language: yaml


Output
------

.. autoclass:: pytest_conda_solvers.models.TestOutput
   :members:
   :undoc-members:

.. literalinclude:: examples/test_output.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.DiffTestOutput
   :members:
   :undoc-members:

.. literalinclude:: examples/diff_test_output.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.DeterminingConstrictingSpecsTestOutput
   :members:
   :undoc-members:
   :exclude-members: constrictions_as_list

When no constrictions are found, ``constrictions`` is null:

.. literalinclude:: examples/constricting_specs_output_empty.yaml
   :language: yaml

When constrictions are present:

.. literalinclude:: examples/constricting_specs_output.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.Constriction
   :members:
   :undoc-members:


Errors
------

The :attr:`~pytest_conda_solvers.models.UnsatisfiableTestSpec.error` field of
:class:`~pytest_conda_solvers.models.UnsatisfiableTestSpec` is a discriminated
union of the three error types below, identified by the ``exception`` field.

.. autoclass:: pytest_conda_solvers.models.UnsatisfiableTestError
   :members:
   :undoc-members:

.. literalinclude:: examples/error_unsatisfiable.yaml
   :language: yaml

An empty ``entries`` list is valid when the solver raises the error but no
specific conflict chain is being asserted:

.. literalinclude:: examples/error_unsatisfiable_empty.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.ResolvePackageNotFoundTestError
   :members:
   :undoc-members:

.. literalinclude:: examples/error_resolve_package_not_found.yaml
   :language: yaml

.. autoclass:: pytest_conda_solvers.models.SpecsConfigurationConflictTestError
   :members:
   :undoc-members:

.. literalinclude:: examples/error_specs_configuration_conflict.yaml
   :language: yaml


Provenance
----------

.. autoclass:: pytest_conda_solvers.models.Provenance
   :members:
   :undoc-members:

.. literalinclude:: examples/provenance.yaml
   :language: yaml


Enumerations
------------

.. autoclass:: pytest_conda_solvers.models.TestChannel
   :members:
   :undoc-members:
   :exclude-members: __str__

.. autoclass:: pytest_conda_solvers.models.TestSubdir
   :members:
   :undoc-members:
   :exclude-members: __str__

.. autoclass:: pytest_conda_solvers.models.ChannelPriority
   :members:
   :undoc-members:
   :exclude-members: __str__
