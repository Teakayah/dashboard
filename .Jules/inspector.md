## 2026-05-25 - Playwright Clipboard Permissions on about:blank
**Learning:** Calling `dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)` immediately after test startup fails with "Permission can't be granted to opaque origins" because `dz.url` is `about:blank` before `page.goto()` is called.
**Action:** Always call `page.goto(TARGET_URL)` before granting origin-specific permissions in Playwright tests.
## 2026-05-26 - Assertions for Error Cases
**Learning:** Testing error handling (like `subprocess.CalledProcessError`) should not only verify the fallback return value but also assert that the mocked function was called with the exact expected arguments that led to the error.
**Action:** Add `assert_called_once_with` to mock exception scenarios to ensure the correct code path and arguments triggered the failure.
