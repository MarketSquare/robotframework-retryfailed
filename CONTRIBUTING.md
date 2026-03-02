# Contributing to robotframework-retryfailed

Thanks for helping improve the RetryFailed listener! This project is intentionally small, so the
workflow is simple and scripted. The steps below explain how to set up an environment, run
tooling, and publish a release.

## 1. Environment setup
1. Use Python 3.8+.
2. Create a virtual environment and install the dev extras:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
   The `dev` extra installs flit, mypy, ruff, robocop, check-manifest, twine, and Robot Framework
   add-ons used in the acceptance suites.
3. Install the pre-commit hooks (optional but recommended):
   ```bash
   pre-commit install
   ```

## 2. Linting & formatting
- **Python formatting**: `ruff format .`
- **Python linting**: `ruff check .`
- **Static typing**: `mypy src`
- **Robot Framework linting**: `robocop check --include *.robot --include *.resource`
- **Robot Framework formatting**: `robocop format --include *.robot --include *.resource`
- **Pre-commit (full suite)**: `pre-commit run --all-files`

The same settings live in `pyproject.toml`, so CI and local runs stay aligned. Prefer running the
standalone commands when iterating quickly, and fall back to the pre-commit aggregate before
delivering work.

## 3. Tests
All regression coverage is provided by the acceptance suites under `atest/`. Run them from the
repository root with the listener installed in editable mode:
```bash
robot -d results --listener RetryFailed:10:True:TRACE atest/01_SimpleTestSuite.robot
robot -d results --listener RetryFailed:10:True:TRACE atest/02_KeywordRetryListener.robot
```
Inspect `results/output.xml` and `results/log.html` to confirm retries are recorded correctly.

## 4. Release workflow
1. Bump `__version__` inside `src/RetryFailed/__init__.py`.
2. Verify the manifest and build artifacts:
   ```bash
   check-manifest --update
   flit build
   twine check dist/*
   ```
3. Upload to PyPI (after any manual smoke tests):
   ```bash
   flit publish
   ```
   The helper script `./createPip_whl_tar.sh` automates the same sequence with a keypress between
   verification and upload.

Please open an issue before large or breaking changes so we can align on direction. Happy hacking!
