
## 2026-10-18 - [Batch DuckDB-Wasm Table Creation Queries]
**Learning:** Using `Promise.all()` to concurrently execute multiple schema-modifying queries (like `CREATE OR REPLACE TABLE`) in DuckDB-Wasm causes excessive IPC overhead across the WebWorker boundary.
**Action:** Combine multiple schema-modifying queries into a single newline-separated string and execute them in one `conn.query()` call to minimize IPC roundtrips and improve performance.
