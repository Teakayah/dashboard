
## 2026-10-31 - [Optimize regex searches on large strings]
**Learning:** Running regex searches on multi-megabyte HTML files with inline JSON datasets is extremely slow.
**Action:** When searching for simple presence of library names or patterns, use Python's `in` operator with common substrings as a fast-path pre-check to bypass the expensive regex overhead for missing patterns.
