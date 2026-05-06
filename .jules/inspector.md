## 2024-05-18 - Fix pluralization in build_html
**Learning:** Adding test coverage can surface latent bugs like incorrect pluralization logic. Here, `f'{count} analysis{"" if count == 1 else "es"}'` was resulting in "2 analysises" instead of "2 analyses".
**Action:** Always verify string manipulations by adding edge case tests (e.g., 0, 1, 2) when adding coverage to functions generating user-facing text, and don't hesitate to fix minor bugs discovered during the process.
