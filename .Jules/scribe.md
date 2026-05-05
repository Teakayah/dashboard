## 2025-05-02 - Marker-Based HTML Snippet Injection Pattern
Learning: The codebase frequently utilizes a regex pattern `r'\s*<!-- [marker](?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /[marker](?:-v\d+)? -->)?'` for replacing generated HTML blocks (like responsive styling blocks). The version matching (`(?:-v\d+)?`) handles backward-compatible cleaning of old injected snippets before new ones are inserted.

Action: Future enhancements or additions of dynamic content into HTML templates should follow this non-destructive update pattern, using versioned markers (e.g. `<!-- marker-v2 -->`) and compiling these complex matching expressions to improve clarity and avoid repeating identical regex strings in multiple logic branches.

## 2026-05-05 - StatsCan Value Symbols Mapping
**Learning:** Statistics Canada uses specific string symbols in their CSV 'VALUE' cells (like '..', 'x', 'F', 'E', 'r', 'p') to indicate missing, suppressed, or unreliable data, which should be mapped to `null` during extraction to avoid parsing errors.
**Action:** When working with StatsCan CSV parsing, always check for these specific string symbols and document them to prevent confusing `"ValueError: could not convert string to float"` errors for downstream developers.
