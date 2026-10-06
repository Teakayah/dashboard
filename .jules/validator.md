## YYYY-MM-DD - [Title]
Coverage Gap: [What lacked testing or failed randomly]
Learning: [Why it was difficult to test or why it flaked]
Assertion: [How to reliably test this pattern next time]
## 2023-10-26 - [Flaky UI Test Timeout Fix]
Coverage Gap: `test_canadian_dashboard_province_view_height_stabilizes` and `test_flood_dashboard_height_stabilizes` in `test_usability.py`
Learning: Hardcoded timeouts (`page.wait_for_timeout`) used in a loop to wait for page height stabilization leads to flaky tests, as UI changes and JS callbacks (like Chart.js resize events) might take longer depending on system load and CI environment differences.
Assertion: Instead of arbitrary sleep periods, use Playwright's `page.wait_for_function(...)` to continually poll the state of `document.documentElement.scrollHeight` directly within the browser until it remains stable across multiple intervals.
