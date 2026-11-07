## 2024-11-07 - [DuckDB-Wasm IPC Overhead]
**Learning:** In DuckDB-Wasm, executing many queries concurrently via `Promise.all()` introduces substantial IPC overhead between the main thread and the WebWorker.
**Action:** Combine multiple schema-modifying queries (e.g., `CREATE OR REPLACE TABLE`) into a single batch query string joined by newlines (if they already have trailing semicolons) and execute it with a single `conn.query()` call to eliminate this overhead.
