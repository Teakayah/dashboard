## 2025-05-02 - Marker-Based HTML Snippet Injection Pattern
Learning: The codebase frequently utilizes a regex pattern `r'\s*<!-- [marker](?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /[marker](?:-v\d+)? -->)?'` for replacing generated HTML blocks (like responsive styling blocks). The version matching (`(?:-v\d+)?`) handles backward-compatible cleaning of old injected snippets before new ones are inserted.

Action: Future enhancements or additions of dynamic content into HTML templates should follow this non-destructive update pattern, using versioned markers (e.g. `<!-- marker-v2 -->`) and compiling these complex matching expressions to improve clarity and avoid repeating identical regex strings in multiple logic branches.

## 2025-05-02 - Document StatCan missing value symbols in data cleaner
**Learning:** Statistics Canada datasets use specific symbolic strings ('..', 'x', 'F', 'E', 'r', 'p') to represent various missing or special data states (e.g., Suppressed, Unreliable). These were previously undocumented 'magic strings' in the `_clean` parser function.
**Action:** Documented these specific symbols directly in the `_clean` docstring in `deployment/rebuild_analyses.py` to demystify this domain-specific knowledge for future maintainers.

## 2026-05-05 - StatsCan Value Symbols Mapping
**Learning:** Statistics Canada uses specific string symbols in their CSV 'VALUE' cells (like '..', 'x', 'F', 'E', 'r', 'p') to indicate missing, suppressed, or unreliable data, which should be mapped to `null` during extraction to avoid parsing errors.
**Action:** When working with StatsCan CSV parsing, always check for these specific string symbols and document them to prevent confusing `"ValueError: could not convert string to float"` errors for downstream developers.
## 2024-05-08 - Time-Series Data Normalization
**Learning:** Analysis pages dynamically bind their dataset to global variables like `window.DATA` or `window.RAW`. However, the underlying data objects have disparate shapes (e.g., `{year, value}`, `{date, pop}`). The centralized utility functions in `assets/analysis_utils.js` implicitly expect a normalized `{x, y}` coordinate format. This mismatch is bridged by a heuristic normalization layer inside `getActiveData()`.
**Action:** Always ensure that time-series data passed directly to utility functions like `calculateGrowth` or `getSummary` is explicitly mapped to the `{x, y}` coordinate format if it bypasses `getActiveData()`.
