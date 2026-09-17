## 2024-11-20 - Optimize Sample Loading
**Learning:** DuckDB-Wasm operations over the WebWorker boundary have significant sequential IPC roundtrip latency.
**Action:** When performing independent file registrations and schema creations (e.g., loading samples), execute them concurrently with `Promise.all` instead of sequentially awaiting each.
