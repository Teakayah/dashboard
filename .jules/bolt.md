## 2024-05-24 - Async UI operations
**Learning:** When performing optional, heavy heuristic analyses (like generating instant chart previews) after a core UI action (like loading a file), awaiting the operation can unnecessarily block the critical UI path and reduce perceived responsiveness.
**Action:** Fire-and-forget the asynchronous operation (e.g., `generateInstantCharts().catch()`) rather than `await`ing it to avoid blocking the critical UI path and reducing perceived latency.
