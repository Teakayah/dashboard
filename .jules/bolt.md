## 2026-10-29 - Optimize StatCan Data Rebuilds
**Learning:** Moving heavy I/O tasks like reading CSV files to `concurrent.futures.ThreadPoolExecutor.map` dramatically improves performance over sequential execution. Also, aliasing dictionary methods (e.g. `get = row.get`) inside hot loops handling millions of executions saves constant lookup overhead.
**Action:** For heavy file manipulations, parse files asynchronously/concurrently where possible. Always look for method lookups in large inner loops that can be hoisted.
