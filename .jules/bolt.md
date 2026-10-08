## 2026-10-08 - [Pre-compile strip_responsive regex]
**Learning:** To optimize Python performance (e.g., in scripts like `generate_index.py`), repeatedly compiling regular expressions using `re.compile()` inside tight loops (like iterating over files) incurs redundant evaluation overhead.
**Action:** Pre-compile regular expressions at the module level using `re.compile()` and reuse them, avoiding multiple compilations.
