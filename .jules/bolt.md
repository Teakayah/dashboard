## 2024-05-24 - Batching DuckDB Queries
**Learning:** In DuckDB-Wasm, combining multiple schema-modifying queries into a single string and executing them in one `conn.query()` call significantly minimizes IPC overhead across the WebWorker boundary, compared to executing them concurrently via `Promise.all()`.
**Action:** Always batch schema-modifying queries using `.join('\n')` (or `;\n` if lacking semicolons) to reduce WebWorker IPC overhead.
