## 2026-05-02 - CSV Parsing Throughput Optimization
**Learning:** When parsing large CSV datasets in Python (like StatCan files), using `csv.DictReader` directly is significantly faster than using generator expressions to pre-strip all row values. Pre-stripping fields incurs massive overhead because it runs across all columns and rows before any conditions are evaluated.
**Action:** Use `csv.DictReader`, manually strip only the headers/fieldnames if needed, and rely on evaluating `.strip()` conditionally and on-demand within iteration logic (optimally combined with short-circuiting high-cardinality checks).
## 2025-02-28 - Optimize Sequential HTTP Requests with ThreadPoolExecutor
**Learning:** Sequential HTTP network calls in tight loops represent a major source of I/O blocking performance bottlenecks.
**Action:** When a loop fetches multiple independent resources over HTTP, use `concurrent.futures.ThreadPoolExecutor` to execute the requests in parallel to massively improve execution speed (e.g. going from ~1.18s to ~0.51s for 5 network requests).
