## 2026-05-02 - CSV Parsing Throughput Optimization
**Learning:** When parsing large CSV datasets in Python (like StatCan files), using `csv.DictReader` directly is significantly faster than using generator expressions to pre-strip all row values. Pre-stripping fields incurs massive overhead because it runs across all columns and rows before any conditions are evaluated.
**Action:** Use `csv.DictReader`, manually strip only the headers/fieldnames if needed, and rely on evaluating `.strip()` conditionally and on-demand within iteration logic (optimally combined with short-circuiting high-cardinality checks).

## 2024-05-24 - Short-circuiting high-cardinality checks in tight loops
**Learning:** When evaluating multiple filter conditions over large datasets (e.g. `all(row.get(k) == v for ...)`), placing the most selective condition (high-cardinality) first and using explicit short-circuiting drastically improves performance, as it skips evaluating common conditions (like dates or regions) for 90%+ of the data that will be rejected anyway. Additionally, avoid blanket `.strip()` calls if `v` has no trailing spaces.
**Action:** Order filter rules so that the most selective / restrictive criteria are evaluated first. In Python, replace `all(generator)` with an explicit loop `for k, v in filter_items` to cleanly control evaluation order and avoid generator overhead.
