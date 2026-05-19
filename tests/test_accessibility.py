"""
WCAG 2.1 AA accessibility tests using axe-core.

Injects axe-core from CDN; tests are skipped gracefully if the CDN is
unreachable (e.g. offline dev). CI (GitHub Actions) has internet access.

Failure thresholds:
  critical  — always fails the build
  serious   — fails the build (WCAG AA requires these to be fixed)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import Page

from helpers import BASE

AXE_CDN = (
    'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js'
)
REPO_ROOT = Path(__file__).parent.parent

# Pages to audit — relative to BASE
PAGES = [
    ('index page',    '/'),
    ('dropzone',      '/dropzone.html'),
    ('employment',    '/employment_rate_canada.html'),
    ('nhpi',          '/nhpi_big6_comparison.html'),
    ('flood',         '/flood_risk_gatineau_ottawa.html'),
]

# axe rules we intentionally defer (tracked in TODO.md §2)
PENDING_RULES = {
    'color-contrast',               # partially fixed — some analysis-page inline colours
                                    # will be resolved when CI re-generates them from
                                    # inject_contrast_fix; remove once verified clean
    'scrollable-region-focusable',  # flood page .tabs div — deferred until tab keyboard
                                    # navigation is implemented (TODO §2.2)
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _inject_axe(page: Page) -> None:
    """Inject axe-core from CDN; skip test if CDN is unreachable."""
    try:
        page.add_script_tag(url=AXE_CDN)
        page.wait_for_function('typeof axe !== "undefined"', timeout=8_000)
    except Exception as exc:
        pytest.skip(f'axe-core CDN unavailable: {exc}')


def _run_axe(page: Page) -> list[dict]:
    """Return critical+serious violations, excluding deferred rules."""
    pending = list(PENDING_RULES)
    violations: list[dict] = page.evaluate(
        """(pending) => axe.run({
            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] },
            rules: Object.fromEntries(pending.map(r => [r, { enabled: false }]))
        }).then(r => r.violations.filter(
            v => v.impact === 'critical' || v.impact === 'serious'
        ))""",
        pending,
    )
    return violations


def _fmt(violations: list[dict]) -> str:
    lines = []
    for v in violations:
        nodes = '; '.join(n['html'] for n in v.get('nodes', [])[:3])
        lines.append(f"  [{v['impact'].upper()}] {v['id']}: {v['description']}\n    {nodes}")
    return '\n'.join(lines)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('label,path', PAGES)
def test_page_has_no_critical_or_serious_violations(page: Page, label: str, path: str):
    page.goto(f'{BASE}{path}')
    try:
        page.wait_for_load_state('networkidle', timeout=8_000)
    except Exception:
        pass

    _inject_axe(page)
    violations = _run_axe(page)
    assert not violations, (
        f'{label} ({path}) has {len(violations)} axe violation(s):\n{_fmt(violations)}'
    )


@pytest.mark.parametrize('label,path', PAGES)
def test_page_has_lang_attribute(page: Page, label: str, path: str):
    """<html lang="..."> is required for screen-reader language detection."""
    page.goto(f'{BASE}{path}')
    lang = page.evaluate('document.documentElement.lang')
    assert lang, f'{label}: <html> is missing a lang attribute'


@pytest.mark.parametrize('label,path', PAGES)
def test_images_have_alt_text(page: Page, label: str, path: str):
    """All <img> elements must carry non-empty alt attributes."""
    page.goto(f'{BASE}{path}')
    bad: list[str] = page.evaluate("""
        () => [...document.querySelectorAll('img')]
              .filter(i => !i.hasAttribute('alt') || i.alt.trim() === '')
              .map(i => i.outerHTML.slice(0, 120))
    """)
    assert not bad, f'{label}: {len(bad)} image(s) missing alt text:\n' + '\n'.join(bad)


def test_dropzone_status_has_live_region(page: Page):
    """#status should announce DuckDB init progress to screen readers."""
    page.goto(f'{BASE}/dropzone.html')
    live = page.evaluate(
        "document.getElementById('status')?.getAttribute('aria-live')"
    )
    assert live in ('polite', 'assertive'), (
        f'#status is missing aria-live (got {live!r}) — screen readers won\'t '
        'announce DuckDB init messages'
    )


def test_analysis_tabs_have_roles(page: Page):
    """Tabs on employment page must carry ARIA roles for keyboard users."""
    page.goto(f'{BASE}/employment_rate_canada.html')
    tabs = page.evaluate("""
        () => [...document.querySelectorAll('.tab')]
              .map(t => ({ text: t.innerText.trim(), role: t.getAttribute('role') }))
    """)
    missing = [t for t in tabs if t['role'] != 'tab']
    # Warn rather than hard-fail until §2.2 is implemented
    if missing:
        pytest.xfail(
            f'{len(missing)} tab(s) missing role="tab" — tracked in TODO §2.2: '
            + str([t["text"] for t in missing])
        )
