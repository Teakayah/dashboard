## 2026-09-21 - Playwright Sync vs Async Assertions
Coverage Gap: Flaky UI tests resulting from synchronous method calls
Learning: Combining synchronous locator methods (like `locator.inner_text()`) with standard `assert` statements (e.g., `assert 'text' in locator.inner_text()`) for dynamic elements can cause flaky timeouts.
Assertion: Use native auto-retrying assertions like `expect(locator).to_contain_text(re.compile('text', re.IGNORECASE))` instead of sync getters + basic asserts.
