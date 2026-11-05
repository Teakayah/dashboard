## 2024-11-05 - [Batching Schema-Modifying DuckDB Queries]
**Learning:** Executing multiple schema-modifying queries (like `CREATE OR REPLACE TABLE` or `DROP TABLE`) concurrently via `Promise.all(queries.map(q => conn.query(q)))` causes excessive IPC overhead across the WebWorker boundary.
**Action:** Combine the schema-modifying queries into a single string delimited by `;\n` and execute them in a single `conn.query()` call to minimize IPC roundtrips and prevent valid SQL parsing errors.
