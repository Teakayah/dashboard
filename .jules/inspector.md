## 2026-10-06 - Measuring frontend JS coverage with pytest-cov
**Learning:** When using `pytest-cov` to run Playwright tests, attempting to measure the coverage of frontend JavaScript files (e.g., `pytest --cov=assets/fullscreen.js`) fails with a `CoverageWarning: Module was never imported` because `pytest-cov` only profiles Python code, not JS executed within the headless browser.
**Action:** Do not use `pytest-cov` to attempt to collect code coverage metrics for frontend JavaScript files; it is only effective for Python scripts.
