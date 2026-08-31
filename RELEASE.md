# Releasing

Releases are built from version tags by the `Release` GitHub Actions workflow.
The workflow builds the wheel and source distribution once, uploads the same
files to a draft GitHub release and PyPI, and requests PyPI attestations. It
makes the GitHub release public only after the PyPI upload succeeds.

## Repository configuration

The PyPI trusted publisher uses these values:

- Owner: `conda-incubator`
- Repository: `pytest-conda-solvers`
- Workflow: `release.yml`
- Environment: `pypi`

The GitHub Actions environment `pypi` is restricted to version tags. Immutable
releases are enabled in the repository settings, so published release tags and
assets cannot be changed.

## Publish a release

1. Update `CHANGELOG.md` with the version and release date, then merge the
   release preparation.
2. Update the local `main` branch:

   ```bash
   git switch main
   git pull --ff-only
   git rev-parse HEAD
   ```

3. Confirm the required checks passed for that exact commit.
4. Create an annotated version tag from the tested commit and push it:

   ```bash
   git tag -a 0.1.0 -m "pytest-conda-solvers 0.1.0"
   git push origin 0.1.0
   ```

5. Follow the `Release` workflow. It will build and check the distributions,
   create the draft release, upload its assets, publish to PyPI through trusted
   publishing, and make the GitHub release public.
6. Confirm the release is public on GitHub and PyPI, then install it into a
   clean conda environment and confirm pytest loads the plugin:

   ```bash
   conda create -n pytest-conda-solvers-release \
     conda conda-libmamba-solver pip pytest
   conda run -n pytest-conda-solvers-release \
     python -m pip install --no-cache-dir pytest-conda-solvers==0.1.0
   set -o pipefail
   release_check_dir="$(mktemp -d)"
   conda run -n pytest-conda-solvers-release \
     --cwd "$release_check_dir" \
     pytest --trace-config --collect-only 2>&1 | \
     grep -F "pytest_conda_solvers.plugin"
   ```

Replace `0.1.0` with the version being released. If a workflow job fails after
the draft is created, do not move the tag or edit the draft manually. Use
**Re-run failed jobs**. If PyPI has the version but the GitHub release remains a
draft, re-run only the failed `Publish GitHub Release` job.

Never move a release tag or replace files for a published version. If an
artifact must change after publication, prepare a new version and tag.
