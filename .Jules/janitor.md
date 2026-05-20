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

## 2024-05-20 - DuckDB SQL Injection Prevention
**Learning:** Found a potential SQL injection vulnerability in `dropzone/app.js` where raw user input from an SQL editor (`sqlInput.value`) was directly interpolated into a `CREATE TEMPORARY TABLE` statement before an export. While DuckDB-Wasm runs locally, an arbitrary string could contain multiple statements (e.g. `SELECT * FROM tbl; DROP TABLE tbl`), allowing unintended local database mutations.
**Action:** Replaced the two-step temporary table export logic with a safer, single-step `COPY (${safeSql}) TO ...` structure. By wrapping the stripped user query in parentheses, it acts strictly as a subquery, safely throwing a syntax error on multiple statements rather than executing them.
