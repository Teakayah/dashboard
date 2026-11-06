## 2026-11-06 - Playwright Timeout Swallowing
Coverage Gap: Blind exception handling in Playwright `wait_for` functions could silently swallow real crashes (like connection drops or browser crashes) by catching generic Exceptions.
Learning: Expected network timeouts should be the only errors swallowed when waiting for slow assets to settle. Broad exceptions hide systemic test failures.
Assertion: Always import `TimeoutError as PlaywrightTimeoutError` from `playwright.sync_api` and specifically catch it instead of a bare `Exception`.
