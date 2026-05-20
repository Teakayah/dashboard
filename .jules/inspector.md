## 2026-05-11 - Mocking pathlib dynamically loaded modules

**Learning:** When using `importlib` to dynamically load a script as a module, standard `unittest.mock.patch` might need to be applied broadly to the original imported classes (like `pathlib.Path.exists` or `pathlib.Path.read_text`) rather than the local module's imported alias, because the dynamic loading can bypass some patching mechanics if not careful.

**Action:** When dynamically loading scripts for testing, use `patch('pathlib.Path.exists')` to safely intercept file system checks across the script execution without dirtying the test runner's state.

## 2026-05-20 - Playwright Flakiness with Arbitrary Timeouts
**Learning:** Hardcoded `page.wait_for_timeout()` calls (e.g. `page.wait_for_timeout(400)`) in UI tests often lead to flaky test failures on slower CI environments because rendering can occasionally take slightly longer than the hardcoded delay.
**Action:** Always replace `wait_for_timeout` with deterministic and auto-retrying waits, such as `page.wait_for_selector(..., state='visible')` or `page.wait_for_function(...)` to ensure conditions are met regardless of the runner's speed.
