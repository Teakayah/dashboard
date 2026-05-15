# Project Instructions for Claude

This file mirrors `GEMINI.md` — both documents are the contract for AI agents working on this repository. Read `TODO.md` before proposing changes; it lists the current critical bugs (DuckDB-Wasm init, "Quick Insights" toolbar, accessibility contrast, analysis-page dark mode) and you should not regress them.

## 1. Project at a glance

- **Public site:** `https://teakayah.github.io/dashboard/` (GitHub Pages from `main`).
- **Stack:** Static HTML + vanilla JS + Chart.js + Grid.js + DuckDB-Wasm. Python pipeline (`deployment/`) regenerates artifacts.
- **No build step, no framework.** Treat the generated `*.html` files at the root as build output, not source.

## 2. Repository map

```
deployment/         Python pipeline (regenerates index, analyses, feed, previews)
dropzone/           Drop-Zone front-end + vendored DuckDB-Wasm / Grid.js
assets/             theme.css, fullscreen.js
scripts/            One-off utilities, benchmarks
tests/              pytest + Playwright (Python only; front-end is uncovered)
*.html, index.html, Generated; see §3 for the commit policy
feed.xml, previews/
```

## 3. Git workflow

- `main` — deployed; CI commits regenerated artifacts here.
- `integration` — target for all human / agent PRs.
- Feature branches branch from and target `integration`. Squash-merge.
- CI (`.github/workflows/ci-automerge.yml`) runs on PRs into `main` from `integration`: pytest → merge → regenerate → push.
- **Generated files (`index.html`, root `*.html`, `feed.xml`, `previews/`, `favicon.ico`, `descriptions.json`) live on `main` only.** Don't commit them from feature branches. Edit the source (in `deployment/` and `source/`) and let CI render.
- Exception: `dropzone.html` at root is source and may be edited on feature branches.

## 4. Coding rules (the ones that have been violated)

1. **Accessibility is mandatory.** WCAG AA contrast (≥ 4.5:1 for body text). Do not introduce `#bbb`, `#aaa`, `#999`, `#888` on light backgrounds, or `rgba(255,255,255,0.45)` on dark.
2. **Use theme tokens.** `var(--text)`, `var(--text-muted)`, `var(--bg)` from `assets/theme.css`. Never hardcode `body { background:#…; color:#… }` per page — it breaks dark mode (this is exactly why the analysis pages render badly under `prefers-color-scheme: dark`).
3. **No `alert()` in user flows.** Use inline status panels with `aria-live="polite"`.
4. **Feature-detect.** `navigator.share`, `navigator.clipboard`, `webkitdirectory`, service workers — always with fallbacks.
5. **Service worker discipline.** Any change to cached assets must bump a `CACHE_VERSION` and delete stale caches on `activate`. Stale SW caches are the most common cause of "the site is broken" reports.
6. **DuckDB-Wasm init is fragile.** Changes to `dropzone/app.js init()`, the vendor bundle, or `sw.js` must be verified end-to-end (clean profile, `#status` reaches "DuckDB Ready"). Add a Playwright test rather than relying on manual checks.
7. **Preserve SRI hashes** on external scripts (cf. commit `61d4478`). Do not swap vendored libs for CDN URLs without justification.
8. **Public-facing — verify in a browser** before claiming a UI change works. If you cannot, say so explicitly.

## 5. Testing

- `pytest tests/` — Python-side only. Front-end is uncovered (TODO §4).
- Add a Playwright test next to any front-end change you make. Tests passing does not equal feature working when no test exercises the feature.

## 6. AI-agent posture

This repo has accumulated churn and dead code from multiple agents (`palette/`, `validator/`, `janitor/`, `bolt-`, `scribe-`, `jules/`). When acting as an agent here:

- One concern per PR, small and focused. No drive-by reformatting.
- No new features unless asked — prefer closing items in `TODO.md`.
- Prefer **deletion** when consolidating duplicated code from prior agent passes.
- Never auto-merge without a human review path.
- Update `TODO.md` when you complete or invalidate an item there.

## 7. Tools

When researching or refactoring at scale, prefer the MCP tools to avoid burning context:

- `mcp__gemini-mcp__rank_files` — rank candidates before reading.
- `mcp__gemini-mcp__universal_search` / `semantic_search` — repo Q&A.
- `mcp__knowledge-mcp__kb_query` — local KB (repo ingested under `dashboard,project`).
- `mcp__ollama-mcp__*` — local LLM for cheap summarization.

## 8. Where to start if you've just been invoked

1. `cat TODO.md` — current open issues.
2. `git log --oneline -20` — recent activity.
3. Find the smallest item in `TODO.md` that matches the user's intent and propose a focused fix.
