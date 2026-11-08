## 2024-11-08 - Minimize IPC overhead with joined SQL statements
**Learning:** DuckDB-Wasm uses WebWorkers, resulting in IPC overhead for every query executed. Concurrent schema-modifying queries (e.g., `CREATE TABLE`) via `Promise.all(queries.map(conn.query))` causes massive bottlenecks and can even crash the worker on complex initialization logic.
**Action:** Always combine schema queries using `.join(';\n')` and send them to `conn.query(combinedQuery)` in a single IPC roundtrip instead of iterating or using `Promise.all()`.
