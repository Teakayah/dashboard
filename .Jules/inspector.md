## 2024-05-24 - Missing Tests for `extract_emp_jobs`
**Learning:** `extract_emp_jobs` logic is handled under the variant name `empJobs` in the central extraction engine `extract_statcan_data`. Testing this functionality directly requires using the variant rather than an isolated function.
**Action:** When asked to test specific variants or specific functions in `rebuild_analyses.py`, always check if they are mapped inside `extract_statcan_data` and write the test specifically targeting the underlying extraction logic via the correct variant identifier.
