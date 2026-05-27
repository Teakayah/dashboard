## 2026-05-25 - Playwright Clipboard Permissions on about:blank
**Learning:** Calling `dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)` immediately after test startup fails with "Permission can't be granted to opaque origins" because `dz.url` is `about:blank` before `page.goto()` is called.
**Action:** Always call `page.goto(TARGET_URL)` before granting origin-specific permissions in Playwright tests.
## 2026-05-27 - DuckDB Database Export Playwright Testing
**Learning:** The database export feature in DuckDB-Wasm, which uses `db.copyFileToBuffer` to create an object URL, was completely untested. We need to use Playwright's `expect_download` context manager to assert the export works since it bypasses typical API calls.
**Action:** Add test coverage for complex WASM file blob exports using Playwright's download interception and verify file size to ensure no empty artifacts are produced.
