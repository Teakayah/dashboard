## 2024-10-24 - Optimize CSV Parsing with LRU Cache
**Learning:** Processing datasets with highly repetitive string values (e.g., common null placeholders like '..', 'x', 'F', or empty strings) benefits greatly from caching type conversions.
**Action:** Apply `@functools.lru_cache` to string-cleaning/type-conversion functions when reading large, repetitive CSV files.
