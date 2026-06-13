## 2025-05-02 - Marker-Based HTML Snippet Injection Pattern
Learning: The codebase frequently utilizes a regex pattern `r'\s*<!-- [marker](?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /[marker](?:-v\d+)? -->)?'` for replacing generated HTML blocks (like responsive styling blocks). The version matching (`(?:-v\d+)?`) handles backward-compatible cleaning of old injected snippets before new ones are inserted.

Action: Future enhancements or additions of dynamic content into HTML templates should follow this non-destructive update pattern, using versioned markers (e.g. `<!-- marker-v2 -->`) and compiling these complex matching expressions to improve clarity and avoid repeating identical regex strings in multiple logic branches.

## 2025-05-02 - Document StatCan missing value symbols in data cleaner
**Learning:** Statistics Canada datasets use specific symbolic strings ('..', 'x', 'F', 'E', 'r', 'p') to represent various missing or special data states (e.g., Suppressed, Unreliable). These were previously undocumented 'magic strings' in the `_clean` parser function.
**Action:** Documented these specific symbols directly in the `_clean` docstring in `deployment/rebuild_analyses.py` to demystify this domain-specific knowledge for future maintainers.

## 2026-05-05 - StatsCan Value Symbols Mapping
**Learning:** Statistics Canada uses specific string symbols in their CSV 'VALUE' cells (like '..', 'x', 'F', 'E', 'r', 'p') to indicate missing, suppressed, or unreliable data, which should be mapped to `null` during extraction to avoid parsing errors.
**Action:** When working with StatsCan CSV parsing, always check for these specific string symbols and document them to prevent confusing `"ValueError: could not convert string to float"` errors for downstream developers.
## 2024-05-08 - Time-Series Data Normalization
**Learning:** Analysis pages dynamically bind their dataset to global variables like `window.DATA` or `window.RAW`. However, the underlying data objects have disparate shapes (e.g., `{year, value}`, `{date, pop}`). The centralized utility functions in `assets/analysis_utils.js` implicitly expect a normalized `{x, y}` coordinate format. This mismatch is bridged by a heuristic normalization layer inside `getActiveData()`.
**Action:** Always ensure that time-series data passed directly to utility functions like `calculateGrowth` or `getSummary` is explicitly mapped to the `{x, y}` coordinate format if it bypasses `getActiveData()`.

## 2026-05-06 - Document DuckDB-Wasm BigInt serialization workaround
**Learning:** DuckDB-Wasm queries returning values of type `bigint` (e.g., INT64 or HUGEINT) crash standard JSON serialization (`JSON.stringify`) and UI components like Grid.js.
**Action:** When working with DuckDB-Wasm results in the frontend, always document the necessity of safely converting `bigint` values to strings (e.g., `typeof val === 'bigint' ? val.toString() : val`) before passing them to the UI or serializing them, to clarify this important workaround.

## 2026-05-06 - Document DuckDB File Handling logic in dropzone
**Learning:** `handleFiles` in `dropzone/app.js` groups files by directory to support Delta Lake multi-part datasets (which have a `_delta_log` directory) because HTML file inputs flatten directories. `processFile` then infers the correct DuckDB import function (`read_parquet`, `read_csv_auto`, `read_json_auto`) dynamically based on the file extension.
**Action:** When working on file ingestion logic for DuckDB-Wasm in the browser, always document how flattened directory structures are reconstructed for multi-part datasets and how parsing functions are dynamically mapped to extensions.

## 2026-05-06 - Safe HTML Tag Extraction with Regex Backreferences
**Learning:** Extracting content from dynamically named HTML tags (e.g., matching a class name but not knowing if it's a `div`, `span`, or `p`) using regex can lead to premature matching if there are nested tags and a generic `</[a-z]+>` closing tag pattern is used.
**Action:** When extracting tag contents using regex, always capture the opening tag name in a group (e.g., `([a-zA-Z0-9]+)`) and use a backreference (like `\1`) in the closing tag pattern (e.g., `</\1>`). This ensures the regex dynamically matches the exact closing tag corresponding to the opening one, preventing issues with inner elements.

## 2025-05-14 - Document Ollama requirement in README
**Learning:** `deployment/refresh.py` calls `generate_descriptions.py`, which immediately exits if the `.env` file does not exist or lacks `OLLAMA_URL` and `OLLAMA_MODEL` variables. Without an explicit setup step in the README, developers running the default data update pipeline out of the box will encounter confusing errors or fail-fast exits.
**Action:** When adding scripts that require specific `.env` configurations (especially local AI tooling like Ollama) to a standard developer pipeline, always document the `.env.example` setup explicitly in the project's 'Installation' instructions to prevent onboarding friction.

## 2026-05-15 - Documenting the CI/CD Dual-Branch Workflow
**Learning:** The project uses a specific dual-branch workflow (`integration` -> `main`), where `main` is strictly for CI-generated production artifacts and `integration` is for all PRs and AI-agent branches. This wasn't explicitly clear to new contributors, leading to potential issues with committing generated artifacts to the wrong branch.
**Action:** Always ensure repository workflow specifics, especially related to CI/CD and protected branches, are prominently documented in the README under a 'Contributing' or 'Workflow' section to reduce friction and prevent bad commits.


## 2026-05-24 - DuckDB-Wasm OPFS State Rehydration
**Learning:** DuckDB-Wasm can persist databases across browser sessions using the Origin Private File System (OPFS). However, when the page reloads, the DuckDB instance attaches to the OPFS database silently. The frontend UI must explicitly query `information_schema.tables` to discover these persisted tables and re-hydrate the schema displays and workspace state.
**Action:** When implementing persistence with DuckDB-Wasm in the browser, always document the two-step process: DuckDB handles the storage backend, but the frontend must proactively query system tables upon initialization to restore the user's context.
## 2026-05-25 - Extracted duckdb table UI interaction logic
**Learning:** , , and  dynamically rebuild UI select elements based on duckdb queries against information schemas, but lacked JSDoc detailing the prerequisites like requiring 2 loaded tables to activate the join UI.
**Action:** When adding logic that conditionally changes UI based on DuckDB state, always explicitly comment the required table constraints.
## 2026-05-25 - Extracted duckdb table UI interaction logic
**Learning:** `updateJoinUI`, `updateJoinColumns`, and `updateChartBuilderUI` dynamically rebuild UI select elements based on duckdb queries against information schemas, but lacked JSDoc detailing the prerequisites like requiring 2 loaded tables to activate the join UI.
**Action:** When adding logic that conditionally changes UI based on DuckDB state, always explicitly comment the required table constraints.

## 2026-05-27 - Documenting undocumented utility functions in DuckDB dropzone
**Learning:** `insertAtCursor`, `createPreviewCard`, `renderChart`, and `showToast` were heavily used utility functions inside `dropzone/app.js` but lacked JSDoc comments. This required developers to read the function bodies to understand the accepted argument types and behaviors.
**Action:** Always add complete JSDoc block comments to utility functions to clarify their signatures, parameter types, and overall purpose, reducing cognitive load for developers working within the feature.

## 2026-05-27 - Documenting undocumented utility functions and preventing misplaced comments
**Learning:** In `dropzone/app.js`, the `escapeId` function was mistakenly inserted *between* a massive JSDoc comment for `getRows` and the `getRows` function itself, causing IDEs and documentation generators to attach the wrong documentation to `escapeId` and leaving `getRows` (which had a critical explanation about BigInt proxy traps) without correct tooling support.
**Action:** When auditing or reading codebase utility functions, actively check that JSDoc comments are directly adjacent to the functions they describe, and ensure every utility function (like `escapeId`) has its own clear documentation.
## 2026-05-27 - Documenting undocumented utility functions in DuckDB dropzone
**Learning:** `onTableLoaded` and `displayTableSchema` were utility functions inside `dropzone/app.js` that handled important side effects like clearing initial state, triggering instant chart generation, and updating the SQL editor when tables are loaded or described. Lacking JSDoc comments meant developers had to read the function bodies to understand these side effects.
**Action:** Always add complete JSDoc block comments to utility functions to clarify their side effects, parameter types, and overall purpose, reducing cognitive load for developers working within the feature.
