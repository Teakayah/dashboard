## 2026-05-24 - [Optimize Python membership checks with inline sets]
**Learning:** When checking membership against a small, constant collection of strings in Python, using an inline set literal (e.g., `x in {'a', 'b'}`) rather than a tuple provides O(1) lookups instead of O(N). Python's AST compiler optimizes this into a constant `frozenset` at compile-time.
**Action:** Always use inline set literals for constant membership checks in hot paths.

## 2026-05-27 - [Optimize DuckDB-Wasm Arrow Table extraction]
**Learning:** Iterating row-by-row on DuckDB Arrow Table results using `result.get(i)` is slow due to proxy trap overhead. The native `.toArray()` method is significantly faster for extracting rows.
**Action:** Always use `.toArray()` when extracting data from DuckDB-Wasm results before iterating over them if specific processing (like BigInt serialization) is required.

## 2024-05-18 - Fix N+1 subprocess for git times
**Learning:** Checking modification times for many files via individual subprocess git log calls introduces significant overhead. Batching these lookups into a single git log subprocess call drastically speeds up execution. However, when checking timestamps using a pre-fetched dictionary map from git stdout strings, remember to cast Path objects to strings before lookup to prevent implicit cache-misses since `Path("name") != "name"`.
**Action:** Use batched Git queries when retrieving metadata across many paths. Cast keys to string explicitly when matching subprocess string output against pathlib paths.

## 2026-05-28 - [Optimize Grid.js Large Dataset Initialization]
**Learning:** When initializing `gridjs.Grid` with large datasets, mapping an array of plain objects into an array of arrays (e.g., `rows.map(...)`) creates significant CPU and memory overhead.
**Action:** Always pass the plain objects array directly to `data` and configure `columns` to specify `id` keys (e.g., `columns: columns.map(c => ({ id: c, name: c }))`) to utilize Grid.js native object mapping.
## 2026-06-13 - [Grid.js Memory Leak via Re-rendering]
**Learning:** In `dropzone/app.js`, `renderResults` clears the container via `.textContent = ''` and creates a completely `new gridjs.Grid(...).render(...)` instance on every query execution. This fails to properly clean up Grid.js's internal event listeners and memory references from the previous instances, leading to memory leaks and degraded performance over time as users run multiple queries.
**Action:** Store the Grid.js instance in a global variable (e.g., `let gridInstance = null;`). Instead of destroying and recreating the grid on every query, check if `gridInstance` exists. If it does, use `gridInstance.updateConfig({ columns, data }).forceRender();` to reuse the existing instance efficiently.
