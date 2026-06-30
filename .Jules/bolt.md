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
## 2024-05-24 - [Optimize getRows BigInt check]
**Learning:** DuckDB-Wasm `.toArray()` Arrow Struct Proxy mapping incurs expensive CPU overhead when doing a `typeof === 'bigint'` check on every cell. Most schemas don't contain BigInts.
**Action:** Inspect schema fields first (e.g., `bitWidth === 64`, or string names like `Int64`, `Timestamp`, `Time64`, `Decimal`). If no BigInt-like types are found, use a fast-path mapping loop to avoid type checking altogether.
## 2026-06-18 - Fix Grid.js memory leak during dynamic rendering
**Learning:** Re-rendering Grid.js by clearing `.textContent` and instantiating a new `gridjs.Grid` object on every data update leaves uncleaned event listeners, causing a memory leak.
**Action:** Store the Grid instance and use `gridInstance.updateConfig({ columns, data }).forceRender()` instead of replacing the entire grid. Use `.destroy()` when completely clearing the data.
## 2026-06-23 - DuckDB-Wasm Arrow Proxy Extraction Optimization
**Learning:** Iterating over rows returned by DuckDB-Wasm's `.toArray()` is slow because each row object is an Apache Arrow Struct Proxy. Accessing properties via `rowObj[field]` in a loop triggers heavy proxy getter traps for every single cell. The property access trap overhead is the primary bottleneck, not standard type checks.
**Action:** When processing Arrow Struct Proxy objects (e.g., from DuckDB-Wasm `.toArray()`), always call `.toJSON()` on each row object before accessing its fields. This eagerly converts the Proxy into a plain JavaScript object using Arrow's internal optimized path, completely bypassing the proxy getter trap overhead.

## 2024-11-20 - [Bypass DuckDB Arrow Proxy Getter Trap with toJSON()]
**Learning:** When extracting data from DuckDB-Wasm Arrow Table results via `.toArray()`, the returned array contains proxy objects. Iterating over the fields of these proxy objects incurs significant overhead due to the proxy getter trap. Calling `.toJSON()` on the proxy eagerly converts it into a plain JavaScript object using Arrow's internal optimized path, completely bypassing the heavy proxy getter trap overhead for every cell.
**Action:** Always call `.toJSON()` on each row object from `.toArray()` before accessing its fields for optimal performance.
