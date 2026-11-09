## 2024-10-10 - Regex re.IGNORECASE Performance Overhead
**Learning:** Using `re.IGNORECASE` on multiple regex patterns against the same large string is significantly slower than converting the string to lowercase once and running case-sensitive regexes.
**Action:** When matching multiple case-insensitive patterns against a single large payload, use `.lower()` on the payload first and compile patterns without `re.IGNORECASE`.
