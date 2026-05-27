## 2026-05-25 - Playwright Clipboard Permissions on about:blank
**Learning:** Calling `dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)` immediately after test startup fails with "Permission can't be granted to opaque origins" because `dz.url` is `about:blank` before `page.goto()` is called.
**Action:** Always call `page.goto(TARGET_URL)` before granting origin-specific permissions in Playwright tests.

## 2026-05-26 - Testable argument parsing
**Learning:** Using `sys.argv` implicitly in `argparse` requires `monkeypatch` in tests.
**Action:** Always expose an `argv: Optional[list[str]] = None` parameter in `parse_args` to enable robust testing without mocking globals.

## 2026-05-26 - Test cyclical array indexing in UI components
**Learning:** When UI components like cards use modulo operators (`index % len(COLORS)`) to cycle through predefined styles based on an index, these boundaries must be explicitly tested. Often, testing just indices 0, 1, or 2 fails to prove that the wrap-around logic works correctly or prevents `IndexError`.
**Action:** Always add a specific test case that passes an index strictly greater than or equal to the length of the target array (e.g., `len(COLORS)`) and assert that the resulting style perfectly matches the output of `index % len(COLORS)` (like index 0).

## 2026-05-27 - DuckDB Database Export Playwright Testing
**Learning:** The database export feature in DuckDB-Wasm, which uses `db.copyFileToBuffer` to create an object URL, was completely untested. We need to use Playwright's `expect_download` context manager to assert the export works since it bypasses typical API calls.
**Action:** Add test coverage for complex WASM file blob exports using Playwright's download interception and verify file size to ensure no empty artifacts are produced.
