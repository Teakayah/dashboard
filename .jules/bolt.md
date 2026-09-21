## 2024-05-24 - Initializing Bolt Journal
**Learning:** Started journal.
**Action:** Ready to track performance learnings.

## 2024-05-24 - Pipelining SQL queries in DuckDB-Wasm vs combining
**Learning:** In DuckDB-Wasm, executing multiple separate SQL queries sequentially (or concurrently via Promise.all) is significantly slower than combining them into a single SQL statement where possible, because each query incurs IPC overhead across the WebWorker boundary and DuckDB does not support multiple SQL statements in a single `query()` call. By combining 10 separate `SELECT corr(...)` queries into one query with 10 columns, execution time was reduced by >50%.
**Action:** When running multiple aggregations or stats on the same table, combine them into a single SQL query instead of using `Promise.all` with individual queries.

## 2024-05-24 - Unblocking the Critical Path during Data Ingestion
**Learning:** In the Analytical Drop-Zone, automatically generating heuristic chart previews (like correlation matrices) involves executing expensive, aggregate SQL queries on the newly loaded dataset. By `await`ing these chart generation queries inside the main `onTableLoaded` routine, the application artificially extends the "Processing..." loading state and blocks the user from instantly typing their own SQL queries, even though the core dataset is already successfully loaded into DuckDB.
**Action:** When performing optional, heavy heuristic analyses (like instant charts) after a core action (like loading a file), fire-and-forget the async operation (with a `.catch()`) rather than `await`ing it. This moves the expensive operation outside the critical UI blocking path, significantly reducing perceived latency.
