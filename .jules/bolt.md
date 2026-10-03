
## 2026-10-03 - [Pre-compile regular expressions]
**Learning:** To optimize Python performance (e.g., in scripts like `generate_feed.py`), repeatedly evaluating `re.search()` with string patterns inside tight loops incurs redundant evaluation overhead.
**Action:** Pre-compile regular expressions at the module level using `re.compile()` and reuse them, avoiding multiple compilations.
