## 2026-11-09 - Concurrent HTTP Downloads in update_statcan_data
**Learning:** Using list comprehensions for I/O bound tasks like downloading ZIP files sequentially over the network causes a massive I/O bottleneck. Using concurrent.futures.ThreadPoolExecutor.map provides a drop-in replacement that retains the order of elements while executing downloads concurrently.
**Action:** Use concurrent.futures.ThreadPoolExecutor.map to fetch HTTP data in parallel when executing blocking I/O tasks.
