## 2023-10-24 - LRU Cache for repetitive data strings
**Learning:** The Stats Canada dataset contains highly repetitive string values (e.g. '..', 'x', 'F', or repeated values). Re-evaluating these every time in `_clean` has unnecessary overhead.
**Action:** Apply `functools.lru_cache` to the cleaning/type-conversion function when parsing repetitive datasets to reduce redundant computation.
