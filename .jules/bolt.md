## YYYY-MM-DD - Parallelize Sample Data Loading
**Learning:** Sample data registration and initial querying in DuckDB-Wasm was happening sequentially in a loop, triggering sequential IPC cross-worker overhead for each sample table (`read_csv_auto`).
**Action:** Use `Promise.all()` to map sample datasets and execute `conn.query()` in parallel when loading multiple tables simultaneously, substantially decreasing load time by eliminating sequential IPC latency.
