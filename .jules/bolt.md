## 2024-09-24 - Fire-and-forget for heuristic UI actions
**Learning:** Awaiting optional, heavy heuristic analyses (like `generateInstantCharts`) blocks the main thread from updating the critical UI path (like loading query inputs) when data is loaded.
**Action:** When performing optional heavy analyses after core UI actions, fire-and-forget the async operation (e.g., `generateInstantCharts().catch(console.error)`) rather than `await`ing it to reduce perceived latency.
