## 2026-09-23 - Strict CSP limits Playwright page.wait_for_function

**Learning:** When a strict Content-Security-Policy (CSP) without `unsafe-eval` is enforced, Playwright's `page.wait_for_function()` will fail if passed a bare string expression (e.g., `'document.querySelector(...)')` because it relies on `eval` under the hood.

**Action:** Always pass an arrow function string (e.g., `'() => document.querySelector(...)')` to ensure compatibility with strict CSPs and prevent flaky timeouts during frontend verification.
