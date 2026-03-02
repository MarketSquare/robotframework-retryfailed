# robotframework-retryfailed – Copilot Guide

## Architecture
- `src/RetryFailed/retry_failed.py` hosts the entire listener/library; `RetryFailed` exposes ROBOT_LISTENER_API_VERSION 3 and is imported via `RetryFailed` package (see `src/RetryFailed/__init__.py`).
- `KeywordMetaData` snapshots keyword name/source/line so we can reinsert the same `RunningKeyword` when retrying without duplicating registrations.
- `start_test` deep-copies the original `RunningTestCase` and sets `${RETRYFAILED_RETRY_INDEX}`; `end_test` requeues failures by inserting the saved test back into `test.parent.tests` and flagging original results as SKIP.
- `end_suite` and `RetryMerger` (a `robot.api.ResultVisitor`) rewrite the execution tree so persisted output either collapses duplicates or keeps them when `keep_retried_tests=True`.

## Retry semantics
- Tests/tasks opt in via tags like `[Tags]    test:retry(2)` or `task:retry(5)`; missing tags fall back to the constructor’s `global_test_retries` default supplied on the `--listener RetryFailed:<args>` CLI.
- Keyword retries are entirely tag-driven: `[Tags]    keyword:retry(<n>)` on either user keywords or test cases, with `start_keyword` storing metadata and `end_keyword` ensuring only one registration per (name, source, lineno).
- The listener exposes two warning toggles (`warn_on_test_retry`, `warn_on_kw_retry`) that gate whether BuiltIn logs use WARN or INFO when retries happen; preserve these semantics whenever adding new log messages.
- When `log_level` is passed, retries temporarily raise Robot’s log level; always reset through `_original_log_level` before exiting the listener hook to avoid leaking state between tests/keywords.

## Result shaping & messaging
- `message()` intercepts duplicate-test WARNs emitted by Robot and rewrites them into retry status lines so final logs stay meaningful; any new warning flow should piggyback on this formatting pattern (`Retry {x}/{y} of test ...`).
- `output_file()` always rewrites `output.xml` in place via `ExecutionResult.visit(RetryMerger(...))`; if you touch result data structures remember that post-processing happens after Robot finishes.
- HTML links inserted by `_get_keyword_link()` and `_get_test_link()` rely on Robot-generated element ids; keep IDs intact when adjusting result objects.

## Tests & verification
- Acceptance tests live under `atest/`; run both suites locally with `robot -d results --listener RetryFailed:10:True:TRACE atest/01_SimpleTestSuite.robot` and `atest/02_KeywordRetryListener.robot` (scripted in `atest/run_atest.sh`).
- The suites rely on stateful suite variables (`VAR … scope=SUITE/GLOBAL`), so run them serially and reset `${counter_*}` variables when writing new cases.
- There are no unit tests; regression coverage hinges on these Robot suites plus manual log inspection of `output.xml`/`log.html`.

## Development workflow
- Use Python ≥3.8; `pip install -r requirements-dev.txt` installs the project in editable mode plus the `dev` extra (flit, mypy, ruff, robocop, check-manifest, twine).
- Packaging now runs through Flit: bump `__version__` in `src/RetryFailed/__init__.py`, then execute `./createPip_whl_tar.sh` (wraps `flit build`, `twine check`, and `flit publish`).
- `.pre-commit-config.yaml` is authoritative (ruff lint/format, mypy, robocop); the same settings live in `pyproject.toml`, so add new tooling there.

## Contribution conventions
- Prefer pure Python stdlib + Robot APIs; new deps must be justified because the listener is imported inside Robot runs.
- Keep listener hooks fast and side-effect free—no network/file IO inside `start_*`/`end_*` without caching since they run per test/keyword.
- Document any new listener args in both the README table and `atest` tags so behavior stays discoverable.
- When adding retry metadata, key lookups currently use `(kw_name, kw_source, kw_lineno)`; preserve or extend that tuple instead of relying solely on names to avoid clashes between identically named keywords in different files.
