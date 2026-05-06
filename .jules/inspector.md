## 2025-02-28 - Test `empJobs` variant extraction logic

**Learning:** The codebase uses a generic, centralized extraction engine (`extract_statcan_data`) for various Statistics Canada tables and variants, including `empJobs`. When a user requests tests for `extract_emp_jobs`, you should map this to testing the `empJobs` variant of `extract_statcan_data` instead of looking for an isolated function named `extract_emp_jobs` (unless it was explicitly added/refactored, which requires verification).

**Action:** When asked to write tests for data extraction logic, first locate the function or the routing logic responsible for it. Use existing test helpers (like `create_row` in `test_rebuild_analyses.py`) to easily simulate the standardized input format required by the generic extraction engine.
