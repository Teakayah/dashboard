## 2024-08-22 - Memory Leak in DOM Container Clearing
**Learning:** When replacing or clearing the DOM content of a container (e.g., using `container.textContent = ''`) that houses Chart.js `<canvas>` elements, internal event listeners remain active in memory.
**Action:** Explicitly retrieve and destroy the Chart instances first (e.g., `Chart.getChart(canvas).destroy()`) before clearing the container.
