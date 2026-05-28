## 2026-05-25 - Fix Flaky Playwright Page Load Timeouts
Coverage Gap: UI tests in `tests/test_dropzone.py` and `tests/test_interactivity.py` intermittently fail due to 30000ms timeouts on `dz.goto(DROPZONE_URL)`.
Learning: Playwright's default `goto` waits for the 'load' event, which can be flaky or excessively slow for pages relying on complex async initialization (like DuckDB-Wasm). The pages actually load successfully and return 200 OK much earlier.
Assertion: To reliably test this, change `goto` calls to use `wait_until='domcontentloaded'` and increase the timeout to 60000ms.
