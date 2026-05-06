## 2024-05-04 - Fix test_screenshot.py mock command line arguments
**Learning:** When testing a Python script using `argparse` that's invoked dynamically, `sys.argv` defaults to whatever pytest was started with, causing `unrecognized arguments` failures.
**Action:** Patch `sys.argv` in the test to provide predictable command-line arguments for scripts loaded with `importlib.util`.

## 2024-05-24 - extract_meta unit tests
**Learning:** The `extract_meta` function in `generate_index.py` handles complex fallbacks for HTML metadata extraction, including regex-based subtitle truncation and library pattern matching, which are critical for the dashboard index generation.
**Action:** Always ensure rigorous testing of these parsing fallbacks when modifying any HTML extraction logic, specifically utilizing the `load_generate_index_module` helper to dynamically inject mocked module dependencies like `_git_date`.

## 2024-05-24 - Mocking sys.argv for Standalone Python Scripts
**Learning:** When using `pytest` (especially with plugins like `--cov`) to test standalone executable Python scripts that parse arguments via `argparse.ArgumentParser.parse_args()` without explicit argument passing, the script will read `sys.argv` from the test runner. This causes the test suite to fail with "unrecognized arguments" errors.
**Action:** Use `@patch("sys.argv", ["script_name.py"])` on test functions that exercise the `main()` entrypoint of these standalone scripts to isolate them from the test environment.
