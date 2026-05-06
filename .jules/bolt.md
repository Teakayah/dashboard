## 2026-05-02 - CSV Parsing Throughput Optimization
**Learning:** When parsing large CSV datasets in Python (like StatCan files), using `csv.DictReader` directly is significantly faster than using generator expressions to pre-strip all row values. Pre-stripping fields incurs massive overhead because it runs across all columns and rows before any conditions are evaluated.
**Action:** Use `csv.DictReader`, manually strip only the headers/fieldnames if needed, and rely on evaluating `.strip()` conditionally and on-demand within iteration logic (optimally combined with short-circuiting high-cardinality checks).

## 2026-05-02 - Git Metadata Retrieval Batching
**Learning:** File metadata retrieval from Git (e.g., in `generate_feed.py` and `generate_index.py`) using individual `git log` subprocess calls per file creates significant N+1 query overhead.
**Action:** Batch git metadata retrieval for multiple files using `git log --format=TS:%cI --name-only -- [files...]` to fetch all metadata in a single subprocess call, parsing the output to build a lookup dictionary.
