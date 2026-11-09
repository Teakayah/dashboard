## 2026-11-09 - Stop Swallowing Exceptions
Coverage Gap: Blind exception handling swallowed genuine crashes and connectivity errors during UI tests.
Learning: Using `except Exception: pass` for expected timeouts in Playwright tests hides real failures (like browser crashes or connection errors) and violates testing principles.
Assertion: Always specifically catch expected exceptions (e.g., `TimeoutError` from `playwright.sync_api` or `subprocess.CalledProcessError`) to ensure real failures are surfaced and tests remain reliable.
