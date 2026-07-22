## 2026-07-22 - Zip Slip Path Traversal Protection
**Learning:** Found a critical vulnerability edge-case in `deployment/update_statcan_data.py` missing test coverage, where Zip slip path traversal attempts inside a downloaded zip file could silently fail or bypass tests if not asserted properly.
**Action:** Added `test_download_table_path_traversal` using `BytesIO` to create an in-memory zip file with malicious `../` paths, confirming the code properly raises `zipfile.BadZipFile`. Always use mock in-memory payloads for edge-case vulnerability testing.
