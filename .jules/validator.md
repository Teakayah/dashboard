## 2026-10-10 - Refactor Playwright Timeouts for Chart.js Animations
Coverage Gap: End-to-end tests for UI dashboards (`tests/test_usability.py` and `tests/test_analysis_pages.py`) were failing due to hardcoded timeouts and manual polling loops.
Learning: Arbitrary timeouts are unreliable for asynchronous UI rendering, such as layout stabilization or tab activation. Using hardcoded delays makes tests flaky when running locally or inside CI because computation speeds vary.
Assertion: Use Playwright's native `expect(locator).to_have_class` for state transitions and `page.wait_for_function(...)` to continually poll for dynamic rendering updates (like canvas resizing) instead of `page.wait_for_timeout`.
