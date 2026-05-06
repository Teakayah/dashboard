## 2024-05-06 - Missing Test Coverage for git_dates and load_descriptions
Coverage Gap: The `get_git_dates_batched` and `load_descriptions` functions lacked testing.
Learning: When writing tests for modules that import config or are dynamically loaded, using standard fixtures like `monkeypatch` and `tmp_path` provides isolation and prevents the tests from depending on external git behavior or touching disk assets.
Assertion: Used `monkeypatch` and `tmp_path` to inject a mock root and create dummy files, enabling tests to verify behavior predictably without actually interacting with the codebase.

## 2024-05-18 - Improve inject_og_tags coverage in generate_index.py
Coverage Gap: The `inject_og_tags` function in `deployment/generate_index.py` was completely untested, leaving social metadata generation (OG and Twitter properties) and html entity escaping vulnerable to undetected regressions.
Learning: When verifying HTML metadata injection logic, standardizing assertions around string inclusion combined with parameterized mocked environments (e.g., using `monkeypatch` for constant settings) ensures reliable testing across potential site configuration changes and unhandled edge cases like missing `<title>` tags.
Assertion: The test functions check specific metadata strings containing `<meta property="og:title" ...` ensuring correct formatting and safe entity escaping using `assert '<meta ...>' in res`.
