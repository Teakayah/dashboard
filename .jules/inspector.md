## 2026-11-09 - Avoid blind exception handling for expected timeouts
**Learning:** Blind exception handling like `except Exception: pass` when waiting for expected slow network assets can silently swallow real failures such as browser crashes or connection errors.
**Action:** Specifically catch `TimeoutError` from Playwright (`playwright.sync_api.TimeoutError`) to ensure real failures are bubbled up instead of swallowed.
