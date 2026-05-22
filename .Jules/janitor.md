## 2024-05-02 - Removed unused library imports
Learning: Removed unused python standard library imports across the project which acts as dead code.
Action: To apply this next time I can run ruff check --select F401,F841 to verify dead code before running to fix unused variables.

## 2024-05-18 - Clean up unused imports, assignments, and duplicated tests
**Learning:** Found multiple unused imports and duplicate test definitions that caused Ruff to complain. Also found a case where module-level imports were placed below variable definitions.
**Action:** Cleaned up unused assignments and duplicated tests, ordered module-level imports at the top, and fixed other ruff warnings across `tests/` and `benchmark_final_test.py`.

## 2025-05-18 - Safe DOM Manipulation
**Learning:** Found multiple usages of `.innerHTML` for DOM manipulation (clearing, injecting raw strings, and setting single options) which violate best security practices for preventing DOM-based XSS.
**Action:** Replaced `.innerHTML` assignments with safer methods: `.textContent = ''` for clearing elements, `.textContent` for updating text, and used `document.createElement()`, `className`, `.textContent`, and `appendChild()` for constructing new DOM nodes (e.g., in `nhpi_big6_comparison.html` and `dropzone/app.js`). Applied across all frontend files.


## 2025-05-19 - Duplicate tests and improperly placed module imports
**Learning:** Found duplicate test function definitions and improperly placed module-level imports causing linters to complain and creating potential edge case test overrides.
**Action:** Ensured to run linters consistently to catch duplicate blocks and ensure imports are cleanly placed at the top of python files.

## 2026-05-18 - Robust Chart.js Object.defineProperty Override
Learning: An `Object.defineProperty` trap for `window.Chart` implemented within a `window.addEventListener('load', ...)` can miss early initialization if Chart.js is loaded synchronously or executed prior to the `load` event.
Action: Implement `Object.defineProperty` globally and immediately using both `get` and `set` accessors. The `set` logic applies the modifications (e.g. `maintainAspectRatio = false`) to the target class and then stores it in a closure variable.

## 2026-05-22 - Prevent SQL Injection in Export Logic
Learning: When building SQL commands with user input inside DuckDB-Wasm, directly interpolating raw strings (e.g., `CREATE OR REPLACE TEMPORARY TABLE _export_tmp AS ${sqlInput.value.trim()}`) makes the application vulnerable to stacked query injection.
Action: To apply this next time, strip trailing semicolons from the user input and wrap the dynamic portion within parentheses inside a `COPY (<query>) TO ...` command to force it to act purely as a subquery, blocking multiple statement execution.
