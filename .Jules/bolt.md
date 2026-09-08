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
## 2024-05-23 - Arrow Struct Proxy Extraction Performance
**Learning:** DuckDB-Wasm Arrow Struct Proxy extraction has a significant performance bottleneck due to the heavy proxy getter trap overhead for every cell. Accessing `rowObj[field]` on the proxy is slow.
**Action:** Always call `.toJSON()` on each row object returned by `.toArray()` before accessing its fields. This eagerly converts the Proxy into a plain JavaScript object using Arrow's internal optimized path, bypassing the overhead.
## 2024-05-24 - Optimize Arrow Row Proxy Extraction
**Learning:** When processing Arrow Struct Proxy objects (e.g., from DuckDB-Wasm `.toArray()`), calling `.toJSON()` on each row object eagerly converts the Proxy into a plain JavaScript object. This uses Arrow's internal optimized path and completely bypasses the heavy proxy getter trap overhead for every cell during iteration.
**Action:** Always call `.toJSON()` on DuckDB-Wasm Arrow proxy rows before field extraction to bypass proxy getter overhead.

## 2026-06-28 - [Optimize DuckDB-Wasm Arrow Struct Proxy extraction using toJSON]
**Learning:** When processing Arrow Struct Proxy objects (e.g., from DuckDB-Wasm `.toArray()`), the primary performance bottleneck during row mapping is the property access/getter invocation. Modern JS engines optimize type checks efficiently, but the proxy trap overhead on every field access is high. Calling `.toJSON()` eagerly converts the Proxy into a plain JavaScript object using Arrow's internal optimized path, completely bypassing the heavy proxy getter trap overhead for every cell.
**Action:** Always call `.toJSON()` on each row object when iterating rows returned by `.toArray()` from DuckDB-Wasm before accessing its fields to efficiently extract it into a plain object.

## 2026-06-29 - [Optimize DuckDB-Wasm Arrow Struct Proxy extraction]
**Learning:** Iterating over properties of DuckDB Arrow Table results proxies directly is slow due to the heavy proxy getter trap overhead for every cell, even after extracting row objects via `.toArray()`.
**Action:** Always eagerly convert the row Proxy into a plain JavaScript object using `.toJSON()` before accessing its fields to completely bypass proxy overhead.
## 2024-06-30 - Optimize DuckDB Arrow Struct Proxy Extraction
**Learning:** When processing Arrow Struct Proxy objects (e.g., from DuckDB-Wasm `.toArray()`), the heavy property access overhead can be entirely bypassed. Calling `.toJSON()` on each row object converts the Proxy into a plain JavaScript object eagerly using Arrow's internal optimized path, which avoids the heavy proxy getter trap overhead for every cell.
**Action:** When extracting data from DuckDB-Wasm Arrow result proxies, always call `.toJSON()` on the row objects before accessing fields.
## 2024-07-04 - Concurrent Feed Generation
**Learning:** Using list comprehensions for I/O bound tasks like reading local files can be inefficient compared to reading them concurrently. Using `concurrent.futures.ThreadPoolExecutor.map` provides a drop-in replacement that retains the order of elements while executing concurrently.
**Action:** When mapping over items and executing blocking I/O tasks like `Path.read_text()` or `requests.get()`, apply concurrent execution via thread pools instead of sequential processing, especially if the impact is measurable.

## 2026-07-04 - [Arrow Struct Proxy Optimization]
**Learning:** In DuckDB-Wasm, query results returned as Apache Arrow Struct Proxy objects incur massive getter trap overhead for every cell access, causing UI crashes or severe lag during serialization or grid rendering.
**Action:** Extract the rows using `.toArray()` and eagerly convert each row Proxy to a plain JavaScript object using `.toJSON()` before cell iteration, completely bypassing the proxy getter overhead.

## 2026-07-18 - Prevent Grid.js Memory Leaks
**Learning:** Wiping the DOM container (`.textContent = ''`) and creating a new `gridjs.Grid` instance for dynamic data causes severe memory leaks due to uncleaned event listeners.
**Action:** Always maintain a reference to the initialized grid instance. Use `gridInstance.updateConfig({...}).forceRender()` to update data efficiently via its Virtual DOM, and explicitly call `gridInstance.destroy()` before clearing the container.
## 2026-07-28 - Conditionally Bypass BigInt Checks for Arrow Proxies
**Learning:** DuckDB-Wasm queries with large row counts spend significant time executing `typeof val === 'bigint'` checks on every single cell of every row if any column in the table has a BigInt. Because Arrow Proxies are already converted to plain objects via `.toJSON()`, we can just identify which columns are BigInt from the schema, and directly mutate only those specific columns, bypassing full row iteration and redundant `typeof` checks for strings/numbers.
**Action:** When extracting data from Arrow proxies, inspect `result.schema.fields` for 64-bit widths to collect specific BigInt columns. Reuse the plain object from `.toJSON()` (or shallow copy it) and iterate only the known BigInt columns to stringify them.

## 2026-07-30 - Concurrent I/O for Multi-Part Datasets
**Learning:** Sequentially awaiting `file.arrayBuffer()` and `db.registerFileBuffer()` for multi-part datasets (like Delta Lake) causes an O(N) I/O bottleneck in DuckDB-Wasm, severely impacting total load time.
**Action:** Use `Promise.all` with `Array.prototype.map` to concurrently process and register file buffers, maximizing browser I/O throughput.
## 2026-08-14 - Schema Caching reduces IPC overhead
**Learning:** Sequential message processing in DuckDB-Wasm creates excessive IPC overhead. Repeatedly querying schema using DESCRIBE causes redundant delays.
**Action:** Caching the DESCRIBE results in a local Map drastically reduces these redundant IPC roundtrips during table load, chart generation, and UI updates.

## 2026-08-18 - [Optimize DuckDB-Wasm Concurrent Queries]
**Learning:** In single-worker DuckDB-Wasm environments, opening multiple queries (like 'DESCRIBE table') concurrently without caching causes excessive IPC overhead and sequential processing latency. Waiting for results instead of promises causes duplicate work.
**Action:** Implement an in-memory cache for asynchronous operations like DuckDB Wasm queries, caching the `Promise` itself (e.g., `cache.set(key, conn.query(...))`) rather than the awaited result. This ensures concurrent requests await the same pending promise.

## 2026-08-23 - [Cache asynchronous DuckDB profiling queries]
**Learning:** In DuckDB-Wasm, executing multiple async profiling queries sequentially (e.g. `conn.query(SELECT MIN...); conn.query(SELECT ... GROUP BY ...)`) each time a schema column is clicked creates excessive IPC overhead. Furthermore, since column stats are static for the loaded table, redundant queries are completely unnecessary.
**Action:** When implementing an in-memory cache for asynchronous operations like DuckDB Wasm queries, cache the `Promise` itself (e.g., `cache.set(key, (async () => { ... })())`) rather than the awaited result. This ensures that concurrent requests for the same key await the same pending promise, preventing duplicate queries and redundant IPC roundtrips.

## YYYY-MM-DD - [Optimize DuckDB-Wasm Profiling Queries]
**Learning:** In single-worker DuckDB-Wasm environments, sequentially awaiting multiple async queries for the same user action (like clicking a column to profile it) creates unnecessary IPC overhead.
**Action:** When multiple independent queries are needed simultaneously, always execute them concurrently using `Promise.all` to reduce roundtrips across the WebWorker boundary and improve latency.
