def test_help_message(pytester):
    result = pytester.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "conda_solver:",
            "*--conda-solver=CONDA_SOLVER*",
            "*--no-bundled-solver-tests*",
        ]
    )
