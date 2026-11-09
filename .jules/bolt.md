## 2026-10-11 - Cache compiled regex in dynamic function
**Learning:** `_inject_const` dynamically compiled regex patterns on every execution using `re.subn`, leading to redundant performance overhead inside loops handling data extraction.
**Action:** Precompile known regex patterns at the module level in a dictionary (e.g. `RE_CONST_DECLS`) to avoid compilation inside repetitive functions.
