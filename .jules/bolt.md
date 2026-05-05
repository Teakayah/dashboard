## 2026-05-02 - CSV Parsing Throughput Optimization
**Learning:** When parsing large CSV datasets in Python (like StatCan files), using `csv.DictReader` directly is significantly faster than using generator expressions to pre-strip all row values. Pre-stripping fields incurs massive overhead because it runs across all columns and rows before any conditions are evaluated.
**Action:** Use `csv.DictReader`, manually strip only the headers/fieldnames if needed, and rely on evaluating `.strip()` conditionally and on-demand within iteration logic (optimally combined with short-circuiting high-cardinality checks).

## 2026-05-02 - Batched Git Lookups
**Learning:** Calling `subprocess.run(['git', 'log', ...])` for every file individually (N+1 queries) introduces significant subprocess overhead (e.g. going from ~0.7s to ~0.45s by batching for just 4 files).
**Action:** Use `git log --format=TS:%cI --name-only -- [files...]` to batch Git metadata retrieval for multiple files in a single subprocess call.
