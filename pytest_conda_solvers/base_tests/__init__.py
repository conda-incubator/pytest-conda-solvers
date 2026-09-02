import pytest

# pytest only rewrites assert statements in modules it collects as tests.
# These two files are imported as plugin code, so without this registration,
# their asserts fail without offering us any useful detail in the output.
pytest.register_assert_rewrite("pytest_conda_solvers.base_tests.install")
pytest.register_assert_rewrite("pytest_conda_solvers.base_tests.solve")
