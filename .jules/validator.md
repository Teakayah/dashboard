## 2026-11-05 - Avoid Blind Exception Handling in Playwright Wait States
Coverage Gap: Using `except Exception:` to suppress expected timeouts silently swallowed actual browser crashes and unrelated errors.
Learning: Expected timeouts should only catch `TimeoutError`. A broad `Exception` catch block incorrectly handles critical errors.
Assertion: Always import `TimeoutError as PlaywrightTimeoutError` from `playwright.sync_api` and specifically catch `PlaywrightTimeoutError` when awaiting transient page states.
