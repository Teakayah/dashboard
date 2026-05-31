## 2026-05-31 - Optimize Grid.js data rendering
**Learning:** Initializing `gridjs.Grid` with an array of objects that has been `.map()`ped into an array of arrays causes high memory and CPU overhead.
**Action:** Always use the native object mapping feature of Grid.js by providing `data: rows` directly and configuring `columns: columns.map(c => ({id: c, name: c}))`.
