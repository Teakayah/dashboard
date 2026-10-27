## 2026-10-27 - Test timeouts with blind exception handling
Coverage Gap: Wait for networkidle swallows real timeouts.
Learning: Using `except Exception: pass` when waiting for `networkidle` state swallows real errors like `TimeoutError`, causing the test to silently fail to wait, leading to flaky failures in subsequent steps or even failing later assertions incorrectly.
Assertion: When using `page.wait_for_load_state`, explicitly catch `TimeoutError` from Playwright (`from playwright.sync_api import TimeoutError as PlaywrightTimeoutError`) rather than blind `Exception` catching, to avoid masking other failures and ensure real failures crash tests appropriately.
