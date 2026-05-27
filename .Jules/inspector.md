## 2026-05-25 - Playwright Clipboard Permissions on about:blank
**Learning:** Calling `dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)` immediately after test startup fails with "Permission can't be granted to opaque origins" because `dz.url` is `about:blank` before `page.goto()` is called.
**Action:** Always call `page.goto(TARGET_URL)` before granting origin-specific permissions in Playwright tests.
## 2026-05-27 - Support dependency injection for argparse tests
**Learning:** For robust CLI testing, `parse_args` functions should accept an `argv: Optional[list[str]] = None` parameter and pass it to `parser.parse_args(argv)`.
**Action:** Use this pattern to allow tests to pass an argument list directly (dependency injection) instead of relying on `monkeypatch` to manipulate `sys.argv`.
