## 2024-05-04 - Fix test_screenshot.py mock command line arguments
**Learning:** When testing a Python script using `argparse` that's invoked dynamically, `sys.argv` defaults to whatever pytest was started with, causing `unrecognized arguments` failures.
**Action:** Patch `sys.argv` in the test to provide predictable command-line arguments for scripts loaded with `importlib.util`.

## 2024-05-24 - extract_meta unit tests
**Learning:** The `extract_meta` function in `generate_index.py` handles complex fallbacks for HTML metadata extraction, including regex-based subtitle truncation and library pattern matching, which are critical for the dashboard index generation.
**Action:** Always ensure rigorous testing of these parsing fallbacks when modifying any HTML extraction logic, specifically utilizing the `load_generate_index_module` helper to dynamically inject mocked module dependencies like `_git_date`.
