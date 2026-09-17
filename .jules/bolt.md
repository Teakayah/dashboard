## 2024-05-23 - Reduce server readiness polling latency
**Learning:** Using `time.sleep(0.25)` for polling a server startup blocks execution unnecessarily for up to a quarter of a second, even if the server is ready much faster.
**Action:** Replace coarse sleeps with fine-grained sleeps (e.g., `time.sleep(0.01)`) and increase the maximum number of attempts to maintain the original overall timeout duration, reducing latency significantly.
