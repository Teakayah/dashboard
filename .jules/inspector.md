## 2026-05-11 - Mocking pathlib dynamically loaded modules

**Learning:** When using `importlib` to dynamically load a script as a module, standard `unittest.mock.patch` might need to be applied broadly to the original imported classes (like `pathlib.Path.exists` or `pathlib.Path.read_text`) rather than the local module's imported alias, because the dynamic loading can bypass some patching mechanics if not careful.

**Action:** When dynamically loading scripts for testing, use `patch('pathlib.Path.exists')` to safely intercept file system checks across the script execution without dirtying the test runner's state.

## 2026-05-21 - Replace brittle wait_for_timeout with expect_event for dialogs
**Learning:** Relying on hardcoded timeouts like `page.wait_for_timeout(3000)` for UI assertions (like waiting for dialogs) is brittle and can cause flaky tests. Playwright handles dialogs asynchronously, so we should await the explicit event.
**Action:** Use Playwright's built-in `with page.expect_event('dialog') as dialog_info:` to cleanly wait for dialogs and make tests resilient to timing variations.
