## 2024-05-06 - Missing Test Coverage for git_dates and load_descriptions
Coverage Gap: The `get_git_dates_batched` and `load_descriptions` functions lacked testing.
Learning: When writing tests for modules that import config or are dynamically loaded, using standard fixtures like `monkeypatch` and `tmp_path` provides isolation and prevents the tests from depending on external git behavior or touching disk assets.
Assertion: Used `monkeypatch` and `tmp_path` to inject a mock root and create dummy files, enabling tests to verify behavior predictably without actually interacting with the codebase.

## 2024-05-06 - Missing Test Coverage for main loop and table downloading
Coverage Gap: `deployment/update_statcan_data.py` had missing coverage for the core `download_table` logic (which hits the StatCan zip URL) and the `main` script entrypoint which determines when downloads should run (first run vs phase checks vs diff checks).
Learning: Testing a script entrypoint with multiple branches requires carefully patching its external state checks (like `_load_last_checked`, `fetch_changed_since`) as well as the IO effects (`_write_status`, `download_table`). Similarly, testing `zipfile.ZipFile` required mocking the response `.read()` to supply bytes that wouldn't crash `zipfile`'s header check when we expected success, but let it crash naturally for the failure test.
Assertion: Used `unittest.mock.patch` systematically to set `mock_load.return_value` and test all paths of `main()` (first run, max lookback passed, api failure, no updates, partial updates) and injected dummy bytes for `download_table` tests.

## 2024-05-06 - Test inject_back_link
Coverage Gap: Missing tests for inject_back_link function.
Learning: Ensure utility injection functions are well tested for expected cases and idempotency.
Assertion: Added test_inject_back_link_adds_snippet and test_inject_back_link_is_idempotent.

## 2024-05-18 - Improve inject_og_tags coverage in generate_index.py
Coverage Gap: The `inject_og_tags` function in `deployment/generate_index.py` was completely untested, leaving social metadata generation (OG and Twitter properties) and html entity escaping vulnerable to undetected regressions.
Learning: When verifying HTML metadata injection logic, standardizing assertions around string inclusion combined with parameterized mocked environments (e.g., using `monkeypatch` for constant settings) ensures reliable testing across potential site configuration changes and unhandled edge cases like missing `<title>` tags.
Assertion: The test functions check specific metadata strings containing `<meta property="og:title" ...` ensuring correct formatting and safe entity escaping using `assert '<meta ...>' in res`.
