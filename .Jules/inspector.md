
## 2024-05-24 - Mocking sys.argv for Standalone Python Scripts
**Learning:** When using `pytest` (especially with plugins like `--cov`) to test standalone executable Python scripts that parse arguments via `argparse.ArgumentParser.parse_args()` without explicit argument passing, the script will read `sys.argv` from the test runner. This causes the test suite to fail with "unrecognized arguments" errors.
**Action:** Use `@patch("sys.argv", ["script_name.py"])` on test functions that exercise the `main()` entrypoint of these standalone scripts to isolate them from the test environment.
