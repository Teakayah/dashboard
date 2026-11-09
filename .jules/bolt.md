## 2024-05-18 - Minimize WebWorker IPC Overhead for SQL Batching
**Learning:** Executing multiple schema-modifying DuckDB queries (e.g., CREATE TABLE, DROP TABLE) concurrently via `Promise.all()` causes unnecessary IPC overhead across the WebWorker boundary.
**Action:** Batch schema-modifying queries into a single string delimited by newlines (ensuring valid semicolons) and execute them in a single `conn.query()` call to minimize IPC latency. Check if queries already contain semicolons before joining with `;\n` or `\n`.
