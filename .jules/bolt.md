## 2026-05-02 - CSV Parsing Throughput Optimization
**Learning:** When parsing large CSV datasets in Python (like StatCan files), using `csv.DictReader` directly is significantly faster than using generator expressions to pre-strip all row values. Pre-stripping fields incurs massive overhead because it runs across all columns and rows before any conditions are evaluated.
**Action:** Use `csv.DictReader`, manually strip only the headers/fieldnames if needed, and rely on evaluating `.strip()` conditionally and on-demand within iteration logic (optimally combined with short-circuiting high-cardinality checks).

## 2026-05-02 - Git Metadata Retrieval Batching
**Learning:** File metadata retrieval from Git (e.g., in `generate_feed.py` and `generate_index.py`) using individual `git log` subprocess calls per file creates significant N+1 query overhead. Batching this (e.g. going from ~0.7s to ~0.45s for 4 files) significantly improves performance.
**Action:** Batch git metadata retrieval for multiple files using `git log --format=TS:%ci --name-only -- [files...]` to fetch all metadata in a single subprocess call, parsing the output to build a lookup dictionary.

## 2024-05-24 - Short-circuiting high-cardinality checks in tight loops
**Learning:** When evaluating multiple filter conditions over large datasets (e.g. `all(row.get(k) == v for ...)`), placing the most selective condition (high-cardinality) first and using explicit short-circuiting drastically improves performance, as it skips evaluating common conditions (like dates or regions) for 90%+ of the data that will be rejected anyway. Additionally, avoid blanket `.strip()` calls if `v` has no trailing spaces.
**Action:** Order filter rules so that the most selective / restrictive criteria are evaluated first. In Python, replace `all(generator)` with an explicit loop `for k, v in filter_items` to cleanly control evaluation order and avoid generator overhead.

## 2026-05-06 - Avoiding Duplicate CSV Parsing
**Learning:** Parsing the exact same large CSV file (`14100287.csv`, typically ~100k-300k rows) multiple times sequentially (e.g. for extracting different tables/variants) incurs massive duplicate I/O and parsing overhead. Reading it twice effectively doubles the processing time.
**Action:** When extracting multiple subsets (like `empRate` and `empJobs`) from the same underlying large CSV, read and parse the CSV into a single variable first (`rows = _read_csv(csv_path)`), then pass that cached representation to all subsequent extraction functions.
## 2025-05-14 - Optimizing String Strip Overhead in Tight Loops
**Learning:** In heavily repeated loops (e.g., millions of rows), even "cheap" operations like `.strip()` add up. When matching against constants, we can short-circuit these calls using length comparisons and pre-calculating the "cleanness" of the target value. In-place memoization of the stripped value provides significant gains for multi-pass data processing.
**Action:** Always look for ways to memoize cleaning operations in-place if the data structure is mutable and reused across multiple passes or functions.
