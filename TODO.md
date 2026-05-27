# DataDashboard — Project Review & Action Plan

_Last reviewed: 2026-05-15. This file replaces the previous "everything ✅" status report, which was misleading._

## 0. Reality check

The previous TODO claimed "Integration & Persistence Milestone ✅" with 230+ tests covering the project. In practice:

- The test suite covers **only the Python deployment scripts** (`generate_index`, `rebuild_analyses`, `refresh`, `screenshot`, `update_*`). It does **not** exercise `dropzone/app.js`, `assets/analysis_utils.js`, `assets/fullscreen.js`, the service worker, the theme, or any rendered analysis page logic. `test_usability.py` is the only Playwright suite and is narrow.
- The "Accessibility Audit" item is unchecked in practice. Several core color tokens (`#bbb`, `#aaa`, `#94a3b8`, `#999` on light backgrounds) fail WCAG AA contrast.
- DuckDB-Wasm never reaches the "Ready" state in many sessions. The recent `de159bd` fix only handled a missing `delta` extension — it did not address the underlying init flow.
- The "Quick Insights" toolbar (`assets/analysis_utils.js`) is auto-injected into every page that loads `analysis_utils.js` (including `dropzone.html`), reads from `window.DATA || window.RAW` which the rendered analysis pages do not expose in that shape, and uses `alert()` for output. It is effectively broken everywhere.
- The repository has accumulated generated artifacts at the root (`index.html`, `*.html`, `feed.xml`, `previews/`, `descriptions.json`, `__pycache__/`, a stray `# Flood visualization.md`) directly contradicting the policy in `GEMINI.md` §3 ("DO NOT commit generated files").
- The branch / commit history is dominated by AI-agent merges (`palette/…`, `validator/…`, `janitor/…`, `bolt-…`, `scribe-…`, `jules-…`) with little human review. Several merges introduce dead code or duplicated styles.

The rest of this file is the real status.

---

## 1. Critical bugs (P0 — user-visible breakage)

### 1.1 DuckDB-Wasm never finishes initializing
**Where:** `dropzone/app.js:127-162`, `dropzone/vendor/duckdb/*`.

Likely contributing causes (verify each):
- `duckdb.DuckDBAccessMode.READ_WRITE` may be `undefined` in the vendored build, silently passing a bad `accessMode` into `db.open(...)`.
- The Service Worker at `/sw.js` is registered with **no version check or cache-busting**. Stale cached `.wasm` / `.worker.js` from a previous deploy can wedge initialization forever. Add a `CACHE_VERSION` constant and invalidate on activate.
- `import.meta.url`-based worker URLs break under some hosting setups (subpaths). The site is served from `/dashboard/`, not `/`.
- Errors are only surfaced via `statusEl.textContent = 'Error: ' + err.message` — if an exception happens inside the worker post-instantiation, the status text stays at "Initializing worker..." forever.
- `dropzone/vendor/duckdb/duckdb-wasm-browser.mjs` is a stub file containing only the line _"Couldn't find the requested file /dist/duckdb-wasm-browser.mjs in @duckdb/duckdb-wasm."_ — confirm whether it's actually imported anywhere and delete if not.

**Actions:**
- [x] Replace `accessMode: duckdb.DuckDBAccessMode.READ_WRITE` with the numeric constant fallback (`accessMode: duckdb.DuckDBAccessMode?.READ_WRITE ?? 1`) and log the resolved value.
- [x] Add a 30 s init timeout that surfaces a visible, actionable error in `#status` + a "Reload without service worker" button.
- [x] Bump and version the service worker; on `activate`, delete all old caches.
- [ ] Upgrade `@duckdb/duckdb-wasm` from v0.9.1 to the current release and re-vendor the bundles.
- [ ] Delete `duckdb-wasm-browser.mjs` if confirmed unused.
- [ ] Add a Playwright test that loads `dropzone.html` and waits for `#status` to read `DuckDB Ready` within 15 s.

### 1.2 "Quick Insights" toolbar is non-functional
**Where:** `assets/analysis_utils.js`.

- `getActiveData()` looks for `window.DATA` / `window.RAW` and tries to find an array whose first element has `year` or `date` keys, then maps to `{x: year||date, y: value||pop||level}`. The actual analysis pages (`employment_rate_canada.html`, `nhpi_big6_comparison.html`, `flood_risk_gatineau_ottawa.html`) store data in different shapes and under different names — the heuristic finds nothing, so every button emits "No active data series found".
- Output uses `alert()` — inaccessible, blocks the page, looks unprofessional.
- The toolbar is fixed bottom-right with no close button, no keyboard handling, no `role`/`aria-label`, no dark-mode styling.
- It is also injected on `dropzone.html` where it makes zero sense.

**Actions:**
- [ ] Decide whether this feature ships at all. If yes:
  - [ ] Define a single contract — e.g. each analysis page exposes `window.DataDashboard.registerSeries({ id, label, data: [{x,y}] })` — and refactor all pages to use it.
  - [ ] Render results in an inline panel (not `alert()`), with proper focus management and Esc-to-close.
  - [ ] Add `aria-label`, `aria-expanded`, keyboard activation, dark-mode tokens from `theme.css`.
  - [ ] Only auto-inject when at least one series is registered.
- [x] If no: remove `assets/analysis_utils.js` and its `<script>` includes — currently dead UI clutter.

### 1.3 Analysis pages ignore dark mode
**Where:** `employment_rate_canada.html`, `nhpi_big6_comparison.html`, `flood_risk_gatineau_ottawa.html`.

Each page hardcodes `body { background: #f5f5f2; color: #222 }` inline in `<style>`. `theme.css` is loaded after but only overrides specific selectors, so under `prefers-color-scheme: dark` users get a light-grey page with the dark sticky header on top — extremely jarring and large portions of the small text (`#888`, `#999`, `#bbb`) drop below 2:1 contrast.

**Actions:**
- [x] Move all per-page palette to CSS variables in `theme.css`.
- [x] In `deployment/generate_index.py` inject `body{background:var(--bg);color:var(--text)}` override into all analysis pages via `inject_contrast_fix`.
- [x] Snapshot test (Playwright) light and dark renders (implemented in `tests/test_visual_regression.py`).

### 1.4 `navigator.share` button crashes on non-supporting browsers
**Where:** `dropzone.html:198`, plus injected into every analysis page via `rebuild_analyses.py`.

Calling `navigator.share({...})` on Firefox desktop / older Safari throws `TypeError: navigator.share is not a function`. There is no feature detection or fallback to clipboard.

**Actions:**
- [x] Wrap in `if (navigator.share) { … } else { copy URL to clipboard with toast }`.
- [ ] Hide the button entirely when neither share nor clipboard is available.

---

## 2. Accessibility (P0/P1)

The site fails several WCAG 2.1 AA checks. Failures are not edge cases — they affect the default light theme on every page.

### 2.1 Color contrast failures
| Selector | Color | Background | Ratio | Status |
|---|---|---|---|---|
| `.card-date` | `#bbb` | `#fff` | ~1.9 | **fail AA** |
| `.related-link span` | `#bbb` | `#fff` | ~1.9 | **fail AA** |
| `footer a` (index) | `#bbb` | `#f5f5f2` | ~2.0 | **fail AA** |
| `.empty` | `#999` | `#f5f5f2` | ~2.9 | **fail AA** |
| `.header-sub` | `rgba(255,255,255,0.45)` | `#1a1a2e` | ~3.4 | **fail AA** (body text) |
| `.search-bar input::placeholder` | `#aaa` | `#fff` | ~2.5 | **fail AA** |
| `--text-dim: #94a3b8` | — | `#fff` | ~3.0 | **fail AA** for body text |
| analysis pages `.subtitle/.note/.tab` | `#888`, `#999` | `#f5f5f2` | ~3.2/2.9 | **fail AA** |

**Action:**
- [x] Replace `#bbb`, `#aaa`, `#999`, `#888` with `--text-muted: #4b5563` and `--text-dim: #64748b`. Generator injects CSS override into all analysis pages via `inject_contrast_fix`.

### 2.2 Semantics / interaction
- [ ] `dropzone.html` "share" button is rendered via inline `onclick` — keep it but ensure focus styles match the rest of the theme.
- [x] Analysis tabs in `employment_rate_canada.html` use `<div class="tab" onclick="…">` — not keyboard-accessible, no `role="tab"`, no `aria-selected`. Convert to `<button role="tab">` or follow the WAI-ARIA Tabs pattern.
- [ ] The drop-zone has `role="button"` but the inner `<p>` is also clickable and there is no live region for status messages → screen readers don't announce "Loaded N tables". Add `aria-live="polite"` to `#status`.
- [ ] Schema "clickable column" spans (`dropzone/app.js:200`) emulate links with `cursor:pointer + underline` but are spans with `role="button"`. Either make them real `<button>`s or accept the role — but add `:hover` and `:focus-visible` styles and an `aria-pressed`/result announcement after click.
- [x] All `alert()` calls in `dropzone/app.js` (and `analysis_utils.js`) should become inline error/info panels for screen-reader friendliness. (Note: `analysis_utils.js` removed, `app.js` still has some `alert()` for user errors, but critical ones are now inline).
- [x] Added initialization progress bar, column profiling sparklines, and query history visuals to the Analytical Drop-Zone.
- [x] Hide the "Share" button entirely on browsers that support neither `navigator.share` nor `navigator.clipboard`.
- [x] Remove the broken "Quick Insights" toolbar.

### 2.3 Tooling
- [ ] Add `pa11y-ci` or `@axe-core/playwright` and run it in CI against `index.html`, `dropzone.html`, and each analysis page. Fail the build on serious/critical issues.

---

## 3. Repository hygiene (P1)

### 3.1 Generated artifacts checked in
`GEMINI.md` §3 explicitly forbids committing generated files. Currently checked in:
- `index.html`
- `dropzone.html` (injected version)
- `employment_rate_canada.html`, `flood_risk_gatineau_ottawa.html`, `nhpi_big6_comparison.html`
- `feed.xml`, `previews/`, `favicon.ico`, `descriptions.json`
- `__pycache__/`, `deployment/__pycache__/`, `tests/__pycache__/`
- Stray file: `# Flood visualization.md` (note the leading "# " in the filename — almost certainly an artifact of someone pasting a markdown heading as a filename).

**Actions:**
- [x] Policy clarified: generated artifacts live on `main` only. `GEMINI.md` §3 and `CLAUDE.md` §3 updated; `dropzone.html` exception documented.
- [x] `.gitignore` already covers `__pycache__/`, `*.pyc`, `.DS_Store`, `.pytest_cache/` — no tracked files needed removing.
- [x] Deleted `# Flood visualization.md`.
- [x] Renamed `Readme.md` → `README.md`.

### 3.2 AI-agent branch / commit sprawl
Recent history shows long sequences of merges from `palette/…`, `validator/…`, `janitor/…`, `bolt-…`, `scribe-…`, `jules/…`. Some merges introduce dead code (e.g. duplicated styles, unused vars cleaned up two commits later).

**Actions:**
- [ ] Require **human review on every agent PR** before merge into `integration` — currently the CI auto-merges integration → main without gating.
- [ ] Add a branch-name allow-list / required-check rule on `integration`.
- [ ] Squash old agent merges into thematic commits if history becomes a problem for `git blame`.

### 3.3 Dead / suspect code
- [ ] `dropzone/vendor/duckdb/duckdb-wasm-browser.mjs` — appears to be a stub error message, not a module. Verify and delete.
- [ ] `responsive-inject-v6` block at the top of `dropzone.html` and every analysis page does a `Object.defineProperty(window, 'Chart', …)` hack that runs **before** Chart.js loads — confirm it's still needed; if Chart.js defaults are configured elsewhere, remove it.
- [ ] `assets/fullscreen.js` (41 lines) — check that the fullscreen button is actually wired up on every chart, not just some.

---

## 4. Test coverage gaps (P1)

Current tests cover Python deployment scripts. None of the **front-end** is tested. Build out:

### 4.1 Front-end unit / integration
- [x] **DuckDB init** — Playwright: `test_duckdb_init_reaches_ready` in `tests/test_dropzone.py`.
- [x] **Sample load** — `test_load_samples_creates_both_tables` + `test_load_samples_populates_sql_input`.
- [x] **File drop** — `test_csv_file_loads_and_shows_schema` via `set_input_files`.
- [x] **Persistence** — `test_persistence_across_reload` rehydrates schema after full reload.
- [x] **Clear data** — `test_clear_data_wipes_schema` accepts confirm dialog and asserts empty schema.
- [ ] **CSV/JSON export** — execute a query, click Download/Copy, verify resulting payload.
- [ ] **Service worker** — verify cache version increments invalidate old assets.

### 4.2 Visual / accessibility
- [x] axe-core WCAG 2.1 AA CI step — `tests/test_accessibility.py` injects axe-core and fails on critical/serious violations across all pages.
- [ ] Playwright screenshot regression for `index.html` light + dark, and each analysis page light + dark.
- [ ] Keyboard-only navigation test: Tab through the dashboard, verify focus rings are visible and order is logical.

### 4.3 Unit tests for `analysis_utils.js`
- [ ] `calculateGrowth`, `findOutliers`, `getSummary` already have pure-function shape — set up Vitest (or Jest) and add cases for empty, single-element, NaN, all-equal, and very-large arrays.

### 4.4 Python coverage holes
- [ ] `deployment/screenshot.py` is tested but flakily — review and stabilize.
- [ ] `deployment/generate_descriptions.py` test exists but does not cover failure modes (network, malformed HTML).
- [ ] Add a smoke test that runs `deployment/refresh.py` end-to-end against fixture data and asserts the generated HTML has no broken `<script>` SRI mismatches.

---

## 5. Documentation / messaging (P2)

- [x] `Readme.md` → `README.md`, and add a "Known Issues" section pointing here.
- [x] Replace the "230+ tests" / "✅ Done" wording — that's the source of the credibility hit. Be honest about what works and what doesn't.
- [x] Document the dual-branch workflow (`integration` → PR → `main`) for outside contributors.
- [x] Add a one-line description for each analysis page explaining the data source and known caveats.

---

## 6. Suggested order of attack

1. **Stop the bleeding** — disable the broken "Quick Insights" toolbar (§1.2) and the `navigator.share` crash (§1.4). One-line changes, high visible impact.
2. **Fix DuckDB init** (§1.1) — instrument first, then fix. Add the timeout + visible error before chasing the root cause.
3. **Color contrast pass** (§2.1) — search-and-replace tokens, verify with axe.
4. **Dark mode on analysis pages** (§1.3) — fix the generator, regenerate.
5. **Repo cleanup** (§3) — delete artifacts, fix `.gitignore`, rename README.
6. **Test build-out** (§4) — start with the DuckDB init Playwright test (will prevent the next regression of §1.1).
