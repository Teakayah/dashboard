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

## 2026-06-03 - [Optimize Grid.js DuckDB-Wasm array mapping by bypassing BigInt check via Schema]
**Learning:** When passing `result.toArray()` from DuckDB-Wasm, the resulting objects MUST still be mapped to plain objects because Arrow Proxy structs crash Grid.js. However, iterating over all cells to check `typeof val === 'bigint'` is an O(N*M) operation that blocks the main UI thread. Inspecting `result.schema.fields[j].type.bitWidth` allows us to determine if BigInt casting is necessary in O(M) time, unlocking a fast-path mapping loop that avoids the per-cell type check entirely.
**Action:** Always inspect the Arrow schema to determine data types rather than checking runtime values, especially when determining if expensive serialization steps (like BigInt to String conversion) are required in a hot loop.
