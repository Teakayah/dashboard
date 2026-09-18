## 2026-09-18 - Documenting complex regular expressions
**Learning:** Complex Python regular expressions utilizing `re.VERBOSE` and multiline raw strings are highly powerful but can obscure their high-level intent, increasing cognitive load for subsequent developers.
**Action:** Always include a plain-English, high-level summary comment immediately above complex `re.search` blocks (like those extracting HTML tags or attributes) to clarify *what* the regex achieves, complementing the granular inline `re.VERBOSE` comments that explain *how* it works.
