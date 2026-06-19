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

## 2026-05-22 - Extracted duplicated logic and unused code cleanup
**Learning:** Found duplicated inline logic `file.webkitRelativePath || file.name` across several loops in `dropzone/app.js` and removed leftover `console.log` statements used for debugging.
**Action:** Extracted the logic into a top-level helper `const getFilePath = (file) => file.webkitRelativePath || file.name;` and replaced all duplicated inline expressions. Removed debug `console.log`.

## 2026-05-23 - Modernized syntax in dropzone/app.js
**Learning:** Found an old IE6 era `document.selection` being used in `insertAtCursor` in `dropzone/app.js` and modernized it to use nullish coalescing `??`. Also found an opportunity to improve the `getRows` function to preallocate the array `new Array(numRows)` and use standard index-based `for` loops rather than `for...of` loops, as well as minimizing property lookup overhead, which reduces WebAssembly boundary crossing overhead.
**Action:** Replaced `document.selection` with `??`, and modernized `getRows`. Applied in `dropzone/app.js`.
## 2026-05-24 - Service Worker Path Issues
**Learning:** Absolute paths (e.g. `/sw.js`) cause service worker registration to fail when deployed in sub-directories like Github Pages, and relative paths (e.g. `sw.js`) are safer.
**Action:** To apply this next time I can ensure relative paths are used instead of absolute paths.
## 2026-05-26 - Removed redundant Object.defineProperty Chart hack
**Learning:** Found a redundant `Object.defineProperty` Chart.js hack used in `responsive-inject-v6` that isn't needed anymore because `maintainAspectRatio: false` is already manually set in `new Chart` instances.
**Action:** Removed the script block from `deployment/generate_index.py` and updated the marker to `v7` to regenerate all HTML files without it.
## 2024-06-01 - Automated tech debt cleanup with Ruff
Learning: The project uses `ruff` for Python linting. Routine tech debt such as unused module imports, unused variable assignments in mock context managers, and anti-pattern boolean assertions (e.g. `assert x == False`) can be safely and automatically fixed using the `--fix` and `--unsafe-fixes` flags.
Action: To apply this next time, proactively use `ruff check . --fix --unsafe-fixes` to sweep the codebase for easy technical debt wins before resorting to manual string replacements.

## 2026-06-18 - Clean up obsolete code processing functions
**Learning:** Functions related to dead files or features (like removing tags for a script that is completely deleted from the repo) act as dead code. They clutter generation scripts and tests.
**Action:** Identified `strip_analysis_utils` as dead code because `analysis_utils.js` had been previously deleted. Removed the code and the corresponding tests. Addressed F811 shadowing caused by test copy/pasting.
