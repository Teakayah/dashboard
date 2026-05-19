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
## 2024-05-20 - Missing Test Coverage for main in update_flood_data and rebuild_analyses optimization
Coverage Gap: The `main()` logic of `deployment/update_flood_data.py` had no coverage (it performs threading logic and file I/O). The `extract_statcan_data` in `deployment/rebuild_analyses.py` also missed the internal memory optimization branch that utilizes `val.strip() == v` checks.
Learning: When writing tests for threading, we can avoid complex async setups by patching the actual network calls inside the threads (`fetch_gauge_data`, `fetch_precip_data`) to execute quickly with predefined responses, and letting Python's `ThreadPoolExecutor` operate exactly as it does in production, asserting on the final consolidated outcomes. We can also mock the file handle created by `open()` using `mock_open`.
Assertion: Used `mock_open` to capture the final `json.dump` payload across multithreaded network requests to assert `main()` successfully collected and aggregated the results. In `rebuild_analyses`, created specialized dataset inputs that intentionally trigger optimization branches (by injecting extra whitespaces and ensuring length constraints).

## 2024-05-20 - Missing Test Coverage for rebuild_analyses insight generation and NHPI path
Coverage Gap: The `rebuild_employment` function had missing branch and exception coverage for dynamically generating and injecting the `insight` strings based on whether the employment change grew or decreased, or if the `change` key was missing. The `extract_statcan_data` generic logic lacked coverage for its conditional table_id diversion specifically to `extract_nhpi`.
Learning: When verifying conditional behavior inside orchestrator scripts like `rebuild_analyses` that dispatch calls to data processors, defining custom `side_effect` functions on the mocked sub-parsers allows granular control over what specific shapes of data are yielded during test permutations, avoiding the complexity of preparing full mock CSV structures for isolated string-formatting testing.
Assertion: Used `side_effect` with custom inner functions on the `mock_extract_statcan_data` fixture to dynamically return the required `empJobs` variant subsets necessary to traverse each insight generation branch, and mocked `extract_nhpi` to successfully verify that `table_id == "18100205"` correctly diverts the generic pipeline call.
## 2026-05-10 - Replace `wait_for_timeout` with Assertions in UI Tests
Coverage Gap: The UI test for filtering index cards (`test_index_search_filters_cards`) randomly failed due to relying on a hardcoded `page.wait_for_timeout(100)` while the source code debounce is set to 250ms.
Learning: It was failing because arbitrary timeouts in UI tests are brittle, especially when testing components with explicit delays like debounced search inputs. Using hardcoded waits leads to flaky tests across different environments.
Assertion: Always use Playwright's built-in auto-retrying assertions like `expect(locator).to_have_count(expected_count)` or `expect(locator).to_be_visible()` instead of arbitrary sleeps. This guarantees tests are resilient to timing variations and execute as fast as possible.
## 2026-05-19 - test_benchmark_final_test.py
Coverage Gap: Uncovered function `extract_emp_rate_reordered` in `scripts/benchmark_final_test.py` handling list of dicts.
Learning: `extract_emp_rate_reordered` heavily relies on stripping values before checking conditions. The tests needed to verify these spacing anomalies didn't cause failures.
Assertion: Tested happy path with padded and unpadded whitespace, ignored branches on all attributes, and None returns from `_clean`.
