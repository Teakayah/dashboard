## 2026-05-25 - Fix Flaky Playwright Page Load Timeouts
Coverage Gap: UI tests in `tests/test_dropzone.py` and `tests/test_interactivity.py` intermittently fail due to 30000ms timeouts on `dz.goto(DROPZONE_URL)`.
Learning: Playwright's default `goto` waits for the 'load' event, which can be flaky or excessively slow for pages relying on complex async initialization (like DuckDB-Wasm). The pages actually load successfully and return 200 OK much earlier.
Assertion: To reliably test this, change `goto` calls to use `wait_until='domcontentloaded'` and increase the timeout to 60000ms.
## 2026-05-27 - [Tests] Coverage Gap: Missing test coverage for `__main__` and fallback logic in deployment scripts
**Coverage Gap:** The `deployment/` python scripts had very low line coverage on certain files natively since the `if __name__ == '__main__':` execution blocks and network fallback paths were not covered by tests.
**Learning:** `sys.exit` execution scopes block standard testing tools from collecting correctly without explicit handling via tools like `runpy.run_path`, and catching the resulting `SystemExit` appropriately. However, executing `runpy.run_path` skips mocking decorators resulting in potentially dangerous execution of the deployment files and real network requests. We can fix this by writing unit tests to accurately cover missing statements natively (e.g. `mock_urlopen`), and omitting strictly top-level `if __name__ == '__main__':` blocks with `# pragma: no cover`.
**Assertion:** Wrote individual tests for the edge-case fallbacks missing actual coverage explicitly, and properly ignored untested entrypoint block logic.
## 2024-05-29 - Missing coverage in deployment/screenshot.py
Coverage Gap: `deployment/screenshot.py` line 27 and 40-41 missing coverage due to untested `Exception` in `get_git_commit_times_batched` and empty list argument.
Learning: Python `importlib.util.spec_from_file_location('module_name', path)` needs to use a dot separated path (like `'deployment.screenshot'`) matching the coverage run args, or pytest-cov will not record coverage data correctly for dynamic imports.
Assertion: Added unit tests for empty inputs `[]` and `patch('subprocess.run', side_effect=Exception('git error'))` to cover edge cases and error handling in batched fetching logic.
