
## 2026-10-12 - Flaky timeouts in UI state transitions
**Learning:** Using hardcoded delays like `page.wait_for_timeout(2000)` to wait for UI state changes (such as tab switches or canvas rendering) causes tests to run slowly and makes them flaky on slower CI environments.
**Action:** Always replace hardcoded sleeps with Playwright's native auto-retrying assertions (e.g., `expect(locator).to_have_class(re.compile(r'\bactive\b'))`) or `page.wait_for_function` using arrow function strings to immediately poll the DOM for stabilization.
