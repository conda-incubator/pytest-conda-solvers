.. SPDX-License-Identifier: BSD-3-Clause

JSON Schema for Conda Solver Tests
====================================

This page documents the schema for the declarative YAML test files consumed
by pytest-conda-solvers. Each test file deserialises into a
:class:`~pytest_conda_solvers.models.TestModule` containing an ordered list
of test specs. Four test kinds are supported, each represented by a distinct
class and selected via the ``kind`` discriminator field.

.. contents:: On this page
   :local:
   :depth: 1


Top-level container
--------------------

.. autoclass:: pytest_conda_solvers.models.TestModule
   :members:
   :undoc-members:

A test file consists of a single top-level ``tests`` key whose value is a
list of test specs:

.. code-block:: yaml

   tests:
     - name: solve_1_1
       id: B001
       kind: solve
       # ... (see test spec types below)
     - name: test_cuda_fail_1
       id: C003
       kind: unsatisfiable
       # ...


Test specs
----------

Each element of :attr:`~pytest_conda_solvers.models.TestModule.tests` is one
of the four spec types below, identified by its ``kind`` field.

.. autoclass:: pytest_conda_solvers.models.SolveTestSpec
   :members:
   :undoc-members:

A ``solve`` test asserts that the solver reaches a specific final environment
state. Example (B001):

.. code-block:: yaml

   - name: solve_1_1
     id: B001
     provenance:
       node_id: tests/core/test_solve.py::test_solve_1::1
       commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
       url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L58-L124
     kind: solve
     input:
       channels: channel-1
       specs_to_add: numpy
     output:
       final_state:
         - channel-1/${{ arch }}::openssl-1.0.1c-0
         - channel-1/${{ arch }}::readline-6.2-0
         - channel-1/${{ arch }}::sqlite-3.7.13-0
         - channel-1/${{ arch }}::system-5.8-1
         - channel-1/${{ arch }}::tk-8.5.13-0
         - channel-1/${{ arch }}::zlib-1.2.7-0
         - channel-1/${{ arch }}::python-3.3.2-0
         - channel-1/${{ arch }}::numpy-1.7.1-py33_0

.. autoclass:: pytest_conda_solvers.models.SolveForDiffTestSpec
   :members:
   :undoc-members:

A ``solve_for_diff`` test asserts the set of packages unlinked and linked
rather than the complete final environment state. Example (B034):

.. code-block:: yaml

   - name: test_update_deps_2_2
     id: B034
     provenance:
       node_id: tests/core/test_solve.py::test_update_deps_2::2
       commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
       url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L2164-L2232
     kind: solve_for_diff
     input:
       channels:
         - channel-4
         - channel-2
       specs_to_add:
         - flask
       history_specs:
         - flask==0.12
         - jinja2==2.8
       prefix:
         - channel-4/${{ arch }}::python-3.6.6-hc3d631a_0
         - channel-2/${{ arch }}::jinja2-2.8-py36_1
         - channel-2/${{ arch }}::flask-0.12-py36_0
         # ... (full prefix list truncated)
     output:
       unlink_precs:
         - channel-2/${{ arch }}::flask-0.12-py36_0
       link_precs:
         - channel-4/${{ arch }}::flask-0.12.2-py36hb24657c_0

.. autoclass:: pytest_conda_solvers.models.DetermineConstrictingSpecsTestSpec
   :members:
   :undoc-members:

A ``determine_constricting_specs`` test asserts which installed packages are
blocking a requested installation or upgrade. Example (S001):

.. code-block:: yaml

   - name: test_determine_constricting_specs_conflicts
     id: S001
     provenance:
       node_id: tests/core/test_solve.py::test_determine_constricting_specs_conflicts
       commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
       url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L3499-L3535
     kind: determine_constricting_specs
     input:
       channels: channel-1
       specs_to_add: mypkg
       solution_records:
         - record_type: prefix
           package_type: noarch_generic
           name: mypkg
           version: 0.1.0
           channel: test
           subdir: conda-test
           fn: mypkg-0.1.0
           build: pypi_0
           build_number: 1
           paths_data:
           files:
           depends: []
           constrains: []
         - record_type: prefix
           package_type: noarch_generic
           name: mypkgnot
           version: 1.1.1
           channel: test
           subdir: conda-test
           fn: mypkgnot-1.1.1
           build: pypi_0
           build_number: 1
           paths_data:
           files:
           depends:
             - mypkg 0.1.0
           constrains: []
     output:
       constrictions:
         - package: mypkgnot
           constricting_match_spec: mypkg==0.1.0

.. autoclass:: pytest_conda_solvers.models.UnsatisfiableTestSpec
   :members:
   :undoc-members:

An ``unsatisfiable`` test asserts that the solver raises a specific error.
The ``error`` field is a discriminated union — see the `Errors`_ section for
all three error types. Example with ``UnsatisfiableError`` (B005):

.. code-block:: yaml

   - name: test_unsatisfiable_from_channel_1_1
     id: B005
     provenance:
       node_id: conda/testing/solver_helpers.py::SolverTests.test_unsat_from_r1::1
       commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
       url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/conda/testing/solver_helpers.py#L351-L380
     kind: unsatisfiable
     input:
       channels: channel-1
       specs_to_add:
         - numpy 1.5*
         - scipy 0.12.0b1
     error:
       exception: UnsatisfiableError
       entries:
         - numpy=1.5
         - [scipy==0.12.0b1, "numpy[version='1.6.*|1.7.*']"]

Example with ``SpecsConfigurationConflictError`` (I004):

.. code-block:: yaml

   - name: pinned_1_4
     id: I004
     provenance:
       node_id: tests/core/test_solve.py::test_pinned_1::4
       commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
       url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L2356-L2603
     kind: unsatisfiable
     input:
       channels: channel-1
       specs_to_add: scikit-learn==0.13
       prefix: channel-1/${{ arch }}::system-5.8-0
       history_specs: system=5.8=0
       ignore_pinned: false
       pinned_packages:
         - python=2.6
         - iopro<=1.4.2
     error:
       exception: SpecsConfigurationConflictError
       requested_specs:
         - scikit-learn==0.13
       pinned_specs:
         - python=2.6


Input
-----

.. autoclass:: pytest_conda_solvers.models.TestInput
   :members:
   :undoc-members:

Most fields are optional. A minimal input only needs ``specs_to_add``:

.. code-block:: yaml

   input:
     channels: channel-1
     specs_to_add: numpy

A more complete input showing prefix pre-population and solver modifiers:

.. code-block:: yaml

   input:
     channels:
       - channel-4
       - channel-2
     specs_to_add:
       - flask
     history_specs:
       - flask==0.12
     prefix:
       - channel-4/${{ arch }}::python-3.6.6-hc3d631a_0
       - channel-2/${{ arch }}::flask-0.12-py36_0
     pinned_packages:
       - python=3.6
     update_modifier: update_specs
     channel_priority: flexible

.. autoclass:: pytest_conda_solvers.models.PrefixRecord
   :members:
   :undoc-members:

Each entry in ``solution_records`` or ``prefix`` that uses the full record
form (as opposed to a ``channel::name-version-build`` string) looks like:

.. code-block:: yaml

   - record_type: prefix
     package_type: noarch_generic
     name: mypkgnot
     version: 1.1.1
     channel: test
     subdir: conda-test
     fn: mypkgnot-1.1.1
     build: pypi_0
     build_number: 1
     paths_data:
     files:
     depends:
       - mypkg 0.1.0
     constrains: []


Output
------

.. autoclass:: pytest_conda_solvers.models.TestOutput
   :members:
   :undoc-members:

.. code-block:: yaml

   output:
     final_state:
       - channel-1/${{ arch }}::python-3.3.2-0
       - channel-1/${{ arch }}::numpy-1.7.1-py33_0

.. autoclass:: pytest_conda_solvers.models.DiffTestOutput
   :members:
   :undoc-members:

.. code-block:: yaml

   output:
     unlink_precs:
       - channel-2/${{ arch }}::flask-0.12-py36_0
     link_precs:
       - channel-4/${{ arch }}::flask-0.12.2-py36hb24657c_0

.. autoclass:: pytest_conda_solvers.models.DeterminingConstrictingSpecsTestOutput
   :members:
   :undoc-members:
   :exclude-members: constrictions_as_list

When no constrictions are found, ``constrictions`` is null:

.. code-block:: yaml

   output:
     constrictions:

When constrictions are present:

.. code-block:: yaml

   output:
     constrictions:
       - package: mypkgnot
         constricting_match_spec: mypkg==0.1.0

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

.. code-block:: yaml

   error:
     exception: UnsatisfiableError
     entries:
       - numpy=1.5
       - [scipy==0.12.0b1, "numpy[version='1.6.*|1.7.*']"]

An empty ``entries`` list is valid when the solver raises the error but no
specific conflict chain is being asserted:

.. code-block:: yaml

   error:
     exception: UnsatisfiableError
     entries: []

.. autoclass:: pytest_conda_solvers.models.ResolvePackageNotFoundTestError
   :members:
   :undoc-members:

.. code-block:: yaml

   error:
     exception: ResolvePackageNotFound
     entries:
       - package-that-does-not-exist

.. autoclass:: pytest_conda_solvers.models.SpecsConfigurationConflictTestError
   :members:
   :undoc-members:

.. code-block:: yaml

   error:
     exception: SpecsConfigurationConflictError
     requested_specs:
       - scikit-learn==0.13
     pinned_specs:
       - python=2.6


Provenance
----------

.. autoclass:: pytest_conda_solvers.models.Provenance
   :members:
   :undoc-members:

.. code-block:: yaml

   provenance:
     node_id: tests/core/test_solve.py::test_solve_1::1
     commit: 03329e0f4a627c9b9aa92ef34f7f93b9aa83e438
     url: https://github.com/conda/conda/blob/03329e0f4a627c9b9aa92ef34f7f93b9aa83e438/tests/core/test_solve.py#L58-L124


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
