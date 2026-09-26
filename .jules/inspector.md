## 2026-09-26 - Playwright Strict Mode on First Locator
**Learning:** Using `.first` with `.inner_text()` without awaiting a locator state can read pre-rendered values or cause strict mode violations when DOM nodes are identical and dynamically generated.
**Action:** Always assert the visibility of the locator before interacting or extracting text from it, using Playwright's auto-retrying `expect` syntax.
