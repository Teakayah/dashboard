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
## 2024-05-24 - Optimize CSV reading in rebuild_analyses.py
**Learning:** When parsing large CSV datasets, using `csv.reader` with `dict(zip(headers, row))` is significantly faster than using `csv.DictReader`, and avoiding `.strip()` during the load phase provides major performance gains.
**Action:** Always prefer `csv.reader` + `zip` for large files and defer `strip()` to specifically required fields downstream rather than blanketing it during load.

## 2026-05-06 - CSV DictReader Optimization with Backward Compatibility
**Learning:** When optimizing large CSV parsing by replacing `csv.DictReader` with `csv.reader` in Python, standard `zip()` will silently truncate missing column values if a row is shorter than the header list. To preserve the exact `restval=None` backwards compatibility of `DictReader`, use `dict(itertools.zip_longest(headers, row))`. Additionally, when injecting import statements during script patching, always ensure they are placed *below* the script shebang (`#!/usr/bin/env python3`) and any module-level docstrings to prevent breaking executable scripts.
**Action:** When migrating from `DictReader` to `reader` + zip, always use `zip_longest` from `itertools` for safe padding. Verify new import placement in executable Python scripts.
