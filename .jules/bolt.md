## 2026-09-17 - Optimize dummy data generator choice allocations
**Learning:** In large loops, passing newly allocated list literals directly to functions like `random.choice(['A', 'B'])` creates significant overhead because the list object is re-instantiated and garbage collected on every single iteration.
**Action:** Always pre-allocate static reference arrays (e.g., `choices = ['A', 'B']`) outside of high-iteration loops and pass the reference variable to avoid the overhead of continuous object creation.
