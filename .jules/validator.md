## 2026-09-20 - Fix Flaky Inner Text Reads
Coverage Gap: Tests reading `.inner_text()` failed randomly due to capturing default `0.00` values before async DOM data loaded.
Learning: Synchronous playwright methods like `locator.inner_text()` combined with standard `assert` do not wait for DOM state changes, causing flakes on slow-rendering elements.
Assertion: Always synchronize tests by awaiting an auto-retrying assertion (e.g., `expect(locator).not_to_have_text('0.00')`) before extracting a value with `.inner_text()`.
