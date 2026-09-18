## 2026-09-18 - Fix flaky UI test by removing wait_for_timeout
Coverage Gap: test_flood_simulator_updates_multiple_stations used hardcoded timeout instead of waiting for UI to update
Learning: Using inner_text() after page.wait_for_timeout(300) causes flaky tests when DOM rendering is slow.
Assertion: Use Playwright's auto-retrying assertions like expect(locator).not_to_have_text('old_text') before extracting the value.
