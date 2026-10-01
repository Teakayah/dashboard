## 2026-05-15 - [Fire-and-forget Heavy Heuristic Analyses]
**Learning:** Awaiting optional, heavy heuristic analyses (like generating instant chart previews) after a core UI action blocks the critical UI path, resulting in high perceived latency.
**Action:** Execute these operations as fire-and-forget (e.g., `generateInstantCharts().catch()`) rather than `await`ing them.
