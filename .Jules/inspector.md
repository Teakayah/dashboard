## 2025-02-28 - Test `inject_back_link` Function in `generate_index.py`
**Learning:** Testing functions that use regex to modify HTML requires testing happy paths, cases where HTML elements have attributes (e.g. `<body class="...">`), and verifying idempotency.
**Action:** When adding tests for HTML string manipulation functions, ensure you cover scenarios with and without HTML attributes on the targeted tags.
