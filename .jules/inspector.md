## 2024-05-04 - Fix test_screenshot.py mock command line arguments
**Learning:** When testing a Python script using `argparse` that's invoked dynamically, `sys.argv` defaults to whatever pytest was started with, causing `unrecognized arguments` failures.
**Action:** Patch `sys.argv` in the test to provide predictable command-line arguments for scripts loaded with `importlib.util`.

## 2024-05-24 - extract_meta unit tests
**Learning:** The `extract_meta` function in `generate_index.py` handles complex fallbacks for HTML metadata extraction, including regex-based subtitle truncation and library pattern matching, which are critical for the dashboard index generation.
**Action:** Always ensure rigorous testing of these parsing fallbacks when modifying any HTML extraction logic, specifically utilizing the `load_generate_index_module` helper to dynamically inject mocked module dependencies like `_git_date`.

## 2024-05-24 - Mocking sys.argv for Standalone Python Scripts
**Learning:** When using `pytest` (especially with plugins like `--cov`) to test standalone executable Python scripts that parse arguments via `argparse.ArgumentParser.parse_args()` without explicit argument passing, the script will read `sys.argv` from the test runner. This causes the test suite to fail with "unrecognized arguments" errors.
**Action:** Use `@patch("sys.argv", ["script_name.py"])` on test functions that exercise the `main()` entrypoint of these standalone scripts to isolate them from the test environment.

## 2026-05-08 - Fixed build_html plural logic
**Learning:** The string logic for pluralization in `build_html` was previously flawed (`'2 analysises'`).
**Action:** Refactored the logic to use the correct English pluralization (`'analyses'`) and updated corresponding test assertions.

## 2026-05-08 - DuckDB-Wasm Proxy Trap Duplicate Entries Error
**Learning:** Iterating over keys using `Object.keys(row)` on DuckDB-Wasm row proxies can trigger an `ownKeys on proxy: trap returned duplicate entries` error in some environments.
**Action:** Avoid dynamic key iteration on row proxies. Instead, always use the explicit field names from the result schema (`result.schema.fields`) to access data in a loop.

## 2026-05-08 - Relative paths for DuckDB-Wasm bundles
**Learning:** Simple relative paths (e.g., `./vendor/...`) in `MANUAL_BUNDLES` are resolved relative to the **page URL** (the HTML file), not the **script URL**. This causes failures if the HTML and JS files are in different directories (e.g., `ROOT/dropzone.html` vs `ROOT/dropzone/app.js`).
**Action:** Use `new URL('./path/to/asset', import.meta.url).href` to robustly resolve assets relative to the module script itself, ensuring they are found regardless of where the HTML page is located.

## 2024-05-24 - Missing Tests for `extract_emp_jobs`
**Learning:** `extract_emp_jobs` logic is handled under the variant name `empJobs` in the central extraction engine `extract_statcan_data`. Testing this functionality directly requires using the variant rather than an isolated function.
**Action:** When asked to test specific variants or specific functions in `rebuild_analyses.py`, always check if they are mapped inside `extract_statcan_data` and write the test specifically targeting the underlying extraction logic via the correct variant identifier.

## 2025-02-28 - Test `empJobs` variant extraction logic
**Learning:** The codebase uses a generic, centralized extraction engine (`extract_statcan_data`) for various Statistics Canada tables and variants, including `empJobs`. When a user requests tests for `extract_emp_jobs`, you should map this to testing the `empJobs` variant of `extract_statcan_data` instead of looking for an isolated function named `extract_emp_jobs`.
**Action:** When asked to write tests for data extraction logic, first locate the function or the routing logic responsible for it. Use existing test helpers (like `create_row` in `test_rebuild_analyses.py`) to easily simulate the standardized input format required by the generic extraction engine.

## 2024-05-25 - Improve coverage for generic statcan extraction and script entrypoint
**Learning:** Functions like `extract_statcan_data` often have complex routing logic based on `table_id` with specific edge cases (invalid dates, no config, memoization optimizations) that lack explicit test coverage, leading to blind spots. Additionally, standalone script entrypoints (`if __name__ == "__main__":`) are frequently missed by test runners but can be covered safely using `runpy.run_path` alongside proper mocking of `sys.argv` and `sys.exit`.
**Action:** Always identify uncovered branches in generic routing functions and ensure they are tested. When encountering untested script entrypoints, use `runpy.run_path` with appropriate mocks to simulate direct execution without causing the test runner to exit prematurely.
