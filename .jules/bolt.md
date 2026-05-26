## 2026-05-26 - [Optimize DuckDB-Wasm row extraction]
**Learning:** Extracting data from DuckDB-Wasm Arrow tables row-by-row via `result.get(i)` is slow due to proxy trap overhead. The native `result.toArray()` method is approximately 10x faster because it bypasses individual getters, though the result still requires iteration to handle specific type casting (like BigInts).
**Action:** When converting Arrow tables to plain JavaScript objects from DuckDB-Wasm results, always use `result.toArray()` rather than manually iterating and calling `.get(i)`.
