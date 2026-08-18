## 2026-05-25 - Playwright Clipboard Permissions on about:blank
**Learning:** Calling `dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)` immediately after test startup fails with "Permission can't be granted to opaque origins" because `dz.url` is `about:blank` before `page.goto()` is called.
**Action:** Always call `page.goto(TARGET_URL)` before granting origin-specific permissions in Playwright tests.

## 2026-05-26 - Testable argument parsing
**Learning:** Using `sys.argv` implicitly in `argparse` requires `monkeypatch` in tests.
**Action:** Always expose an `argv: Optional[list[str]] = None` parameter in `parse_args` to enable robust testing without mocking globals.

## 2026-05-26 - Test cyclical array indexing in UI components
**Learning:** When UI components like cards use modulo operators (`index % len(COLORS)`) to cycle through predefined styles based on an index, these boundaries must be explicitly tested. Often, testing just indices 0, 1, or 2 fails to prove that the wrap-around logic works correctly or prevents `IndexError`.
**Action:** Always add a specific test case that passes an index strictly greater than or equal to the length of the target array (e.g., `len(COLORS)`) and assert that the resulting style perfectly matches the output of `index % len(COLORS)` (like index 0).

## 2026-05-27 - DuckDB Database Export Playwright Testing
**Learning:** The database export feature in DuckDB-Wasm, which uses `db.copyFileToBuffer` to create an object URL, was completely untested. We need to use Playwright's `expect_download` context manager to assert the export works since it bypasses typical API calls.
**Action:** Add test coverage for complex WASM file blob exports using Playwright's download interception and verify file size to ensure no empty artifacts are produced.

## 2026-05-26 - Assertions for Error Cases
**Learning:** Testing error handling (like `subprocess.CalledProcessError`) should not only verify the fallback return value but also assert that the mocked function was called with the exact expected arguments that led to the error.
**Action:** Always use `mock.assert_called_once_with` when simulating exceptions (like `subprocess.CalledProcessError`) to explicitly verify the mock was called with the exact parameters expected before it threw the error.

## 2026-05-28 - Test Exception Handling Validation
**Learning:** Adding test coverage for exception blocks isn't just about covering lines; it requires asserting *how* the failure was triggered to ensure it's not a generic or unintended exception.
**Action:** Always use `mock.assert_called_once_with` when simulating exceptions (like `subprocess.CalledProcessError`) to explicitly verify the mock was called with the exact parameters expected before it threw the error.

## 2026-06-01 - Python coverage module names for `importlib.util.spec_from_file_location`
**Learning:** If a Python module is imported dynamically in tests using `importlib.util.spec_from_file_location` and the module name doesn't match its relative package path (e.g., using `screenshot` instead of `deployment.screenshot`), `pytest-cov` might report 0% coverage with a `module-not-imported` warning.
**Action:** Always ensure the module name passed to `spec_from_file_location` matches its expected dot-separated package path (e.g., `deployment.script_name`) to enable proper coverage tracking.

## 2026-06-01 - Testing `__main__` entrypoint with `importlib.util`
**Learning:** Dynamic module execution using `importlib.util.spec_from_file_location` bypasses mocks defined for that module in the parent testing context, since `exec_module` initializes it in a fresh namespace. Mocking the script's `main()` function from the parent test before `exec_module` does not mock the module's internal `main()` call inside its `if __name__ == "__main__":` block.
**Action:** Mocking `sys.exit` works for the top-level block, but to avoid executing the module's real `main()`, `sys.argv` mocking or other external mock patterns (or refactoring) should be used if running the real `main()` has side effects.

## 2026-06-03 - [Missing clipboard error handling]
**Learning:** The clipboard API (`navigator.clipboard.writeText`) returns a Promise that must be `.catch()`'d to handle denials or context issues. Silent failures prevent UI toasts from alerting the user. Mocking `navigator.clipboard` using `Object.defineProperty` within `page.evaluate()` is effective for simulating these failures in Playwright tests.
**Action:** Always append `.catch()` blocks to clipboard operations and include tests that mock promise rejections.
## 2026-06-30 - UI Tests: Avoid invoking global UI functions
**Learning:** Calling `page.evaluate("showTab('...')")` caused tests to break when the JS function was removed, even though the UI (buttons and click events) remained functional.
**Action:** Use native Playwright locators and `.click()` to simulate user interactions instead of directly evaluating global JS methods to prevent tight coupling to implementation details.
## 2026-06-28 - Flaky tests due to missing wait options in Playwright's goto
**Learning:** Calling `page.goto(url)` without `wait_until="domcontentloaded"` and a suitable timeout can lead to flaky tests, especially when testing WASM modules or other heavy resources. Playwright tests could fail with timeouts or errors related to opaque origins when trying to grant permissions (e.g., clipboard) because the navigation hasn't completed or has barely started.
**Action:** Always provide explicit wait options like `wait_until="domcontentloaded"` and `timeout=60000` when calling `page.goto()` in Playwright tests to ensure the page is adequately loaded before interacting with elements or granting permissions.

## 2026-07-17 - Testing Playwright File Downloads
**Learning:** Testing file downloads in Playwright requires verifying that the downloaded file is not an empty artifact. Catch-all `try...except Exception: pass` blocks can silently hide download failures.
**Action:** Always assert the file size of the downloaded file using `os.path.getsize(dl.path()) > 0` (ensure to use synchronous `dl.path()` instead of `await dl.path()` in synchronous tests) and avoid swallowing exceptions when testing file downloads.

## 2026-07-25 - Testing CSV File Downloads
**Learning:** Testing file downloads in Playwright requires verifying that the downloaded file is not an empty artifact. Catch-all assertions on the content can mask empty file downloads if the fallback handles empty strings gracefully or if the file isn't verified for size first.
**Action:** Always assert the file size of the downloaded file using `os.path.getsize(dl.path()) > 0` before attempting to read its contents when testing file downloads.

## 2026-07-29 - Testing Event Listener Lambdas in Playwright Mocks
**Learning:** When mocking Playwright objects that accept lambda functions as event handlers (e.g., `page.on("console", lambda msg: ...)`), the lambdas themselves must be explicitly executed in the test using `mock_page.on.call_args_list` to verify their internal behavior (like logging statements) and ensure full coverage.
**Action:** Always extract lambda arguments from mock call logs and invoke them with dummy `MagicMock` event objects to test their inner assertions/side-effects.
## 2026-08-18 - Missing MagicMock in Lambda Tests
**Learning:** When writing tests that extract lambdas from Playwright mocks and use `MagicMock` as dummy objects (e.g., event arguments), `MagicMock` must be explicitly imported in the test file, even if the parent file mocks it or uses `patch`.
**Action:** Always verify that `MagicMock` is imported when explicitly instantiating it for mock arguments to lambda functions extracted from Playwright call args.
