## 2026-09-23 - Fire-and-Forget Heavy UI Heuristics
**Learning:** Awaiting heavy optional heuristic analyses (like generating instant chart previews) after core UI actions (like loading a table) blocks the critical UI path (populating the SQL input) and increases perceived latency.
**Action:** Always fire-and-forget asynchronous operations (e.g., `generateInstantCharts().catch()`) rather than `await`ing them if they are not required for the immediate next UI state.
