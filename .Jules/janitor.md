## 2024-05-02 - Removed unused library imports
Learning: Removed unused python standard library imports across the project which acts as dead code.
Action: To apply this next time I can run ruff check --select F401,F841 to verify dead code before running to fix unused variables.
## 2025-02-24 - Remove innerHTML usage
**Learning:** Found anti-pattern `innerHTML` being used, which could lead to XSS. Refactored it to use safer `textContent`, `insertAdjacentHTML`, and `document.createElement()`.
**Action:** Always prefer `textContent` and explicit DOM generation functions to construct elements securely over setting `innerHTML` directly.
