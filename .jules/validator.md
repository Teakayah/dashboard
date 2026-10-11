## 2026-10-11 - Replace sleep with waitForFunction in Playwright UI Tests
Coverage Gap: Flaky UI tests that relied on `page.wait_for_timeout` loops to wait for asynchronous layout stabilization and Chart.js resize callbacks.
Learning: Hardcoded timeouts cause flaky tests. `page.wait_for_function(...)` is needed to poll the browser state directly for stability.
Assertion: Use `page.wait_for_function(...)` with custom JavaScript to continually poll the target state (like document height) directly within the browser until the condition is met, instead of `page.wait_for_timeout`.
