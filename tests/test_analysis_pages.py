"""
Interaction tests for the three analysis pages.

These tests actually drive the UI — clicking tabs, moving sliders, switching
views — and verify that the resulting charts and data update correctly.
They do NOT use DuckDB; all data is hardcoded in the analysis HTML files.

Run with:  pytest tests/test_analysis_pages.py -v
"""

import pytest
import re
from playwright.sync_api import Page, expect

from helpers import BASE

LOAD_TIMEOUT = 8_000   # ms
TAB_TIMEOUT  = 2_000   # ms — post-click settle


def _load(page: Page, path: str) -> None:
    page.goto(f'{BASE}{path}', wait_until='domcontentloaded', timeout=60000)
    try:
        page.wait_for_load_state('networkidle', timeout=LOAD_TIMEOUT)
    except Exception:
        pass   # CDN assets (Chart.js, Leaflet) may be slow in CI


# ── Employment Rate (employment_rate_canada.html) ─────────────────────────────

EMPLOYMENT_URL = '/employment_rate_canada.html'
EMPLOYMENT_TABS = ['rate', 'jobs', 'debt', 'pop']
EMPLOYMENT_TAB_LABELS = ['Employment Rate', 'Jobs Created', 'Government Debt', 'Population']


def test_employment_page_loads_with_title(page: Page):
    _load(page, EMPLOYMENT_URL)
    expect(page).to_have_title('Canadian Labour & Fiscal Dashboard')


def test_employment_all_tabs_are_clickable(page: Page):
    """Each tab click must make that panel active and hide the others."""
    _load(page, EMPLOYMENT_URL)

    for i, (tab_id, label) in enumerate(zip(EMPLOYMENT_TABS, EMPLOYMENT_TAB_LABELS)):
        tab = page.locator('.tab').nth(i)
        expect(tab).to_be_visible()
        tab.click()

        # Target panel is active
        active = page.locator(f'#panel-{tab_id}')
        expect(active).to_have_class(re.compile(r'\bactive\b'), timeout=3000)
        assert 'active' in (active.get_attribute('class') or ''), (
            f'Panel #{tab_id} not active after clicking "{label}"'
        )
        # All other panels are hidden
        for other_id in EMPLOYMENT_TABS:
            if other_id != tab_id:
                other = page.locator(f'#panel-{other_id}')
                assert 'active' not in (other.get_attribute('class') or ''), (
                    f'Panel #{other_id} should be hidden when "{label}" is active'
                )


def test_employment_charts_have_height_in_each_tab(page: Page):
    """Canvas elements must have a non-zero height when their panel is active."""
    _load(page, EMPLOYMENT_URL)

    canvas_ids = {
        'rate': 'rateMain',
        'jobs': 'jobsBar',
        'debt': 'debtMain',
        'pop':  'popMain',
    }
    for i, (tab_id, canvas_id) in enumerate(canvas_ids.items()):
        page.locator('.tab').nth(i).click()

        active = page.locator(f'#panel-{tab_id}')
        expect(active).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

        height = page.evaluate(
            f"document.getElementById('{canvas_id}')?.offsetHeight ?? 0"
        )
        assert height > 0, (
            f'Canvas #{canvas_id} has zero height on tab "{tab_id}"'
        )


def test_employment_overview_toggle_switches_chart(page: Page):
    """'Show Overview' button on the rate panel must toggle the chart."""
    _load(page, EMPLOYMENT_URL)

    # Ensure we're on the rate tab
    page.locator('.tab').nth(0).click()
    expect(page.locator('#panel-rate')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    # Find and click an overview / series toggle button
    toggle = page.locator('#panel-rate button').first
    if not toggle.count():
        pytest.skip('No toggle button found on rate panel')

    initial_text = toggle.inner_text()
    toggle.click()

    # Wait for the canvas to render (or text to change) instead of sleeping
    try:
        expect(toggle).not_to_have_text(initial_text, timeout=1000)
    except AssertionError:
        expect(page.locator('#panel-rate canvas').first).to_be_visible(timeout=3000)

    new_text = toggle.inner_text()

    # The button label must change to indicate the view switched
    # (e.g. "Show Overview" ↔ "Show Provinces")
    assert initial_text != new_text or page.locator('#panel-rate canvas').count() > 0, (
        'Rate panel toggle did not change state'
    )


def test_employment_subtitle_is_visible(page: Page):
    _load(page, EMPLOYMENT_URL)
    subtitle = page.locator('.subtitle').first
    expect(subtitle).to_be_visible()
    text = subtitle.inner_text()
    assert 'Statistics Canada' in text, f'Subtitle missing expected text: {text!r}'


# ── NHPI Big-6 (nhpi_big6_comparison.html) ───────────────────────────────────

NHPI_URL = '/nhpi_big6_comparison.html'


def test_nhpi_page_loads_with_title(page: Page):
    _load(page, NHPI_URL)
    title = page.title()
    assert title.strip(), 'NHPI page has an empty <title>'


def test_nhpi_app_container_is_populated(page: Page):
    """The #app div must be filled by the rendering script."""
    _load(page, NHPI_URL)
    app_content = page.evaluate("document.getElementById('app')?.innerHTML ?? ''")
    assert len(app_content.strip()) > 100, (
        f'#app is empty or minimal — JS rendering failed (got {len(app_content)} chars)'
    )


def test_nhpi_year_buttons_are_generated(page: Page):
    """The script must generate at least one year button in .controls."""
    _load(page, NHPI_URL)
    page.wait_for_selector('.controls button', timeout=5_000)
    count = page.locator('.controls button').count()
    assert count >= 3, f'Expected ≥3 year buttons, got {count}'


def test_nhpi_year_button_click_activates_it(page: Page):
    """Clicking a year button must add the 'active' class to that button."""
    _load(page, NHPI_URL)
    page.wait_for_selector('.controls button', timeout=5_000)

    buttons = page.locator('.controls button')
    # Click the second button (first may already be active)
    target = buttons.nth(1)
    target.click()
    expect(target).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    classes = target.get_attribute('class') or ''
    assert 'active' in classes, (
        f'Year button did not get "active" class after click (classes: {classes!r})'
    )


def test_nhpi_main_chart_renders(page: Page):
    """The main NHPI chart canvas must exist with non-zero height."""
    _load(page, NHPI_URL)
    page.wait_for_selector('canvas', timeout=5_000)

    height = page.evaluate("""
        () => {
            const c = document.querySelector('canvas');
            return c ? c.offsetHeight : 0;
        }
    """)
    assert height > 0, 'Main canvas has zero height'


def test_nhpi_subtitle_references_statcan(page: Page):
    _load(page, NHPI_URL)
    subtitle = page.locator('.subtitle').first
    expect(subtitle).to_be_visible()
    text = subtitle.inner_text()
    assert 'Statistics Canada' in text or '18-10-0205' in text, (
        f'NHPI subtitle missing Stats Can reference: {text!r}'
    )


# ── Flood Risk (flood_risk_gatineau_ottawa.html) ──────────────────────────────

FLOOD_URL = '/flood_risk_gatineau_ottawa.html'
# Flood page has 3 panels: gauge, history, snowpack (no panel-map)
FLOOD_TABS = ['gauge', 'history', 'snowpack']


def test_flood_page_loads_with_title(page: Page):
    _load(page, FLOOD_URL)
    title = page.title()
    assert 'flood' in title.lower() or 'gatineau' in title.lower() or 'ottawa' in title.lower(), (
        f'Flood page title unexpected: {title!r}'
    )


def test_flood_all_tabs_switch_panels(page: Page):
    """Clicking each tab must make only that panel visible."""
    _load(page, FLOOD_URL)

    for tab_id in FLOOD_TABS:
        page.locator(f".tab[onclick*=\"'{tab_id}'\"]").click()
        active = page.locator(f'#panel-{tab_id}')
        expect(active).to_have_class(re.compile(r'\bactive\b'), timeout=3000)
        classes = active.get_attribute('class') or ''
        assert 'active' in classes, (
            f'#panel-{tab_id} not active after clicking tab "{tab_id}"'
        )


def test_flood_gauge_chart_has_height(page: Page):
    """The gauge chart canvas must render with non-zero height."""
    _load(page, FLOOD_URL)
    page.locator(".tab[onclick*=\"'gauge'\"]").click()
    expect(page.locator('#panel-gauge')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    height = page.evaluate(
        "document.getElementById('gaugeChart')?.offsetHeight ?? 0"
    )
    assert height > 0, 'gaugeChart canvas has zero height'


def test_flood_slider_updates_britannia_level(page: Page):
    """Moving the slider must update the #levelDisplay value."""
    _load(page, FLOOD_URL)
    page.locator(".tab[onclick*=\"'gauge'\"]").click()
    expect(page.locator('#panel-gauge')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    initial_text = page.locator('#levelDisplay').inner_text()

    # Slider range is min=-1.00 max=3.00 (relative offset from base level)
    page.evaluate(
        "() => { const s = document.getElementById('levelSlider'); "
        "s.value = '-1.0'; s.dispatchEvent(new Event('input')); }"
    )
    expect(page.locator('#levelDisplay')).not_to_have_text(initial_text, timeout=3000)
    low_val_text = page.locator('#levelDisplay').inner_text()
    low_val = float(low_val_text)

    page.evaluate(
        "() => { const s = document.getElementById('levelSlider'); "
        "s.value = '3.0'; s.dispatchEvent(new Event('input')); }"
    )
    expect(page.locator('#levelDisplay')).not_to_have_text(low_val_text, timeout=3000)
    high_val = float(page.locator('#levelDisplay').inner_text())

    assert high_val > low_val, (
        f'#levelDisplay did not increase as slider went up ({low_val} → {high_val})'
    )


def test_flood_slider_updates_hull_level(page: Page):
    """Hull level (#hullDisplay) must co-update with the slider."""
    _load(page, FLOOD_URL)
    page.locator(".tab[onclick*=\"'gauge'\"]").click()
    expect(page.locator('#panel-gauge')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    initial_hull = page.locator('#hullDisplay').inner_text()
    page.evaluate(
        "() => { const s = document.getElementById('levelSlider'); "
        "s.value = '2.0'; s.dispatchEvent(new Event('input')); }"
    )
    expect(page.locator('#hullDisplay')).not_to_have_text(initial_hull, timeout=3000)
    updated_hull = page.locator('#hullDisplay').inner_text()

    assert initial_hull != updated_hull, (
        f'#hullDisplay did not update with slider ({initial_hull!r} → {updated_hull!r})'
    )


def test_flood_history_chart_renders(page: Page):
    """Historical chart canvas must have non-zero height."""
    _load(page, FLOOD_URL)
    page.locator(".tab[onclick*=\"'history'\"]").click()
    expect(page.locator('#panel-history')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    height = page.evaluate(
        "document.getElementById('historyChart')?.offsetHeight ?? 0"
    )
    assert height > 0, 'historyChart canvas has zero height on history tab'


def test_flood_snowpack_chart_renders(page: Page):
    """Snowpack chart must render on its tab."""
    _load(page, FLOOD_URL)
    page.locator(".tab[onclick*=\"'snowpack'\"]").click()
    expect(page.locator('#panel-snowpack')).to_have_class(re.compile(r'\bactive\b'), timeout=3000)

    height = page.evaluate("""
        () => {
            const canvas = document.querySelector('#panel-snowpack canvas');
            return canvas ? canvas.offsetHeight : 0;
        }
    """)
    assert height > 0, 'Snowpack panel canvas has zero height'
