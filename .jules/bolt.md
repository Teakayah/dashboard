## 2024-05-20 - Fire-and-forget heavy optional UI operations
**Learning:** Awaiting optional, heavy heuristic analyses (like generating instant chart previews) blocks the critical UI path (such as updating inputs and showing table previews).
**Action:** Fire-and-forget the asynchronous operation (e.g., `generateInstantCharts().catch()`) rather than `await`ing it to avoid blocking the critical UI path and reduce perceived latency.
