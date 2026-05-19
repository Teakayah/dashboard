# Project Instructions for AI Agents (Gemini)

This is a **public-facing** site (`https://teakayah.github.io/dashboard/`). Quality issues land in front of real users. Read `TODO.md` before proposing changes — it lists current critical bugs and ongoing accessibility / hygiene work that should not be regressed.

## 1. What this project is

DataDashboard is a static site that:
- Lists pre-built data analyses (one HTML page per analysis, generated from `source/` data via `deployment/rebuild_analyses.py`).
- Provides an "Analytical Drop-Zone" (`dropzone.html`) for in-browser SQL on user-supplied CSV/JSON/Parquet via DuckDB-Wasm.
- Auto-builds an index page, an Atom feed, OG previews, and PWA assets via a Python pipeline.

Front-end is vanilla JS + Chart.js + Grid.js. No build step. No framework.

## 2. Repository layout

```
deployment/         Python pipeline: generate_index, rebuild_analyses, refresh, screenshot, etc.
dropzone/           Drop-Zone front-end (app.js + vendored DuckDB-Wasm + Grid.js)
assets/             theme.css, fullscreen.js
scripts/            One-off utilities and benchmarks
tests/              pytest + Playwright (Python-side only; front-end is currently untested)
source/             Raw data inputs (not always committed)
*.html, feed.xml,
previews/, index.html  Generated artifacts (see §3)
```

## 3. Git workflow

**Branching:**
- `main` — production, deployed by GitHub Pages. CI commits regenerated artifacts here.
- `integration` — all human + agent PRs target this branch.
- Feature branches branch from and target `integration`.

**Merging:** Squash and merge into `integration`. CI auto-merges `integration` → `main` when a PR from `integration` is opened against `main`.

**Generated artifacts** (`index.html`, the per-analysis `*.html` at the repo root, `feed.xml`, `previews/`, `favicon.ico`, `descriptions.json`):
- These live on `main` only. GitHub Pages serves from the repo root; CI regenerates them on every merge.
- **Never commit generated files from `integration` or feature branches.** Edit the sources in `deployment/` and `source/`, then let CI render the canonical versions on `main`.
- `dropzone.html` at root is source — it may be edited on feature branches.

`.github/workflows/ci-automerge.yml` runs on `pull_request` against `main`. It runs pytest, merges `integration`, regenerates artifacts, and pushes back to `main`.

## 4. Style and behaviour rules

- **Public-facing — no broken features.** If you cannot verify a change in a browser, say so explicitly rather than claiming it works.
- **Accessibility is not optional.** Body text must meet WCAG AA contrast (≥ 4.5:1). `#bbb`, `#aaa`, `#999`, `#888` on light backgrounds and `rgba(255,255,255,0.45)` on dark all fail — do not introduce more.
- **Theme variables, not hex codes.** Use `var(--text)`, `var(--text-muted)`, `var(--bg)`, etc., from `assets/theme.css`. New per-page palettes that hardcode `body { background:#…; color:#… }` break dark mode.
- **No `alert()` in user flows.** Use inline panels with `role="status"` or `aria-live="polite"`.
- **Feature-detect browser APIs.** `navigator.share`, `navigator.clipboard`, service workers, `webkitdirectory` — never call without a fallback.
- **Vendored libraries** live in `dropzone/vendor/`. Do not silently swap to a CDN; preserve SRI hashes on external scripts (see commit `61d4478`).
- **DuckDB-Wasm** initialization in `dropzone/app.js` is fragile. Any change to `init()`, the service worker, or the vendor bundle must be verified end-to-end on a clean profile — confirm `#status` reaches "DuckDB Ready".
- **Service worker (`sw.js`).** Always bump a `CACHE_VERSION` and invalidate old caches on `activate`. Stale caches are the #1 cause of "the site is broken" reports.

## 5. Testing

- `pytest tests/` covers the Python deployment pipeline only.
- Front-end coverage is currently a gap (see `TODO.md` §4). When you add front-end behaviour, add a Playwright test in `tests/test_usability.py` or a sibling file.
- Do not mark a task complete on the basis of tests passing if the tests do not exercise the feature you changed.

## 6. AI-agent specific

This repo has historically accepted PRs from multiple automated agents (`palette/`, `validator/`, `janitor/`, `bolt-`, `scribe-`, `jules/`). The result has been code churn, dead code, and regressions that slipped past auto-merge. When operating as an agent:

- **Small, focused PRs.** One concern per PR. No drive-by reformatting.
- **No new features unless explicitly requested.** Prefer fixing existing TODOs.
- **Read `TODO.md` first.** Do not re-introduce items already flagged as broken.
- **Never auto-merge without a human review path.** If you have permission to merge, still request review.
- **Prefer deletion over addition** when consolidating duplicated code from prior agent merges.

## 7. Tools available

- `mcp__gemini-mcp__*` — Gemini-backed search, ranking, and summarization. Use `rank_files` before reading many candidate files; use `universal_search` and `semantic_search` for codebase questions.
- `mcp__knowledge-mcp__*` — local KB. The repo has been ingested under tags `dashboard,project`; query before re-reading large files.
- `mcp__ollama-mcp__*` — local LLM alternative for cheap summarization.

Use these to keep context costs down on large traversals.
