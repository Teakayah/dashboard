## 2023-10-24 - Pre-compile regex in loops
**Learning:** Compiling regex patterns with `re.compile()` inside loops or frequently called functions (like `inject_responsive`) introduces unnecessary evaluation overhead, especially when processing many files.
**Action:** Always pre-compile regular expressions at the module level when they are used in data processing loops or repeated function calls to eliminate redundant compilation overhead.
