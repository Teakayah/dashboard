"""
Basic usability tests for the DataDashboard site.
Requires: pip install pytest pytest-playwright
          python -m playwright install chromium
"""

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

BASE = 'http://localhost:8765'
REPO_ROOT = Path(__file__).parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def analysis_pages() -> list[str]:
    """Return all root HTML files except index.html."""
    return [
        p.name for p in sorted(REPO_ROOT.glob('*.html'))
        if p.name.lower() != 'index.html'
    ]


# ── Index page ────────────────────────────────────────────────────────────────

def test_index_title(page: Page):
    page.goto(BASE)
    expect(page).to_have_title('DataDashboard')


def test_index_header_visible(page: Page):
    page.goto(BASE)
    expect(page.locator('header h1')).to_be_visible()


def test_index_has_cards(page: Page):
    page.goto(BASE)
    cards = page.locator('.card')
    assert cards.count() > 0, 'Index page has no analysis cards'


def test_index_card_hrefs_are_valid(page: Page):
    page.goto(BASE)
    hrefs = page.locator('.card').evaluate_all(
        'els => els.map(e => e.getAttribute("href"))'
    )
    assert hrefs, 'No cards found'
    for href in hrefs:
        assert href and href.endswith('.html'), f'Card href is invalid: {href!r}'
        assert (REPO_ROOT / href).exists(), f'Card links to missing file: {href}'


def test_index_search_filters_cards(page: Page):
    page.goto(BASE)
    search = page.locator('#search')
    expect(search).to_be_visible()

    total = page.locator('.card').count()
    assert total > 0

    # Type a string that matches nothing → all cards hidden
    search.fill('xyzzznotarealanything')
    page.wait_for_timeout(100)
    visible = page.locator('.card:not(.hidden)').count()
    assert visible == 0, 'Search filter did not hide non-matching cards'

    # Clear → cards reappear
    search.fill('')
    page.wait_for_timeout(100)
    visible = page.locator('.card:not(.hidden)').count()
    assert visible == total, 'Clearing search did not restore all cards'


def test_index_search_finds_match(page: Page):
    page.goto(BASE)
    # Grab the first card's title text and search for part of it
    first_title = page.locator('.card-title').first.inner_text()
    keyword = first_title.split()[0]  # first word of the title
    page.locator('#search').fill(keyword)
    page.wait_for_timeout(100)
    visible = page.locator('.card:not(.hidden)').count()
    assert visible >= 1, f'Search for {keyword!r} hid all cards'


def test_index_footer_github_link(page: Page):
    page.goto(BASE)
    github_link = page.locator('footer a[href*="github.com"]')
    expect(github_link).to_be_visible()
    href = github_link.get_attribute('href')
    assert href and 'github.com' in href


def test_index_footer_rss_link(page: Page):
    page.goto(BASE)
    rss_link = page.locator('footer a[href*="feed.xml"]')
    expect(rss_link).to_be_visible()
    href = rss_link.get_attribute('href')
    assert href and 'feed.xml' in href


def test_index_no_js_errors(page: Page):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_load_state('networkidle')
    assert errors == [], f'JS errors on index: {errors}'


# ── Mobile ────────────────────────────────────────────────────────────────────

def test_index_no_horizontal_scroll_mobile(page: Page):
    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto(BASE)
    scroll_width = page.evaluate('document.body.scrollWidth')
    viewport_width = page.evaluate('window.innerWidth')
    assert scroll_width <= viewport_width + 2, (
        f'Horizontal overflow on mobile: scrollWidth={scroll_width} > viewportWidth={viewport_width}'
    )


def test_index_cards_visible_on_mobile(page: Page):
    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto(BASE)
    expect(page.locator('.card').first).to_be_visible()


# ── Analysis pages ────────────────────────────────────────────────────────────

@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_loads(page: Page, filename: str):
    response = page.goto(f'{BASE}/{filename}')
    assert response is not None and response.status == 200, (
        f'{filename} returned HTTP {response and response.status}'
    )


@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_has_title(page: Page, filename: str):
    page.goto(f'{BASE}/{filename}')
    title = page.title()
    assert title.strip(), f'{filename} has an empty <title>'


@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_has_og_image(page: Page, filename: str):
    page.goto(f'{BASE}/{filename}')
    og = page.locator('meta[property="og:image"]')
    assert og.count() > 0, f'{filename} is missing og:image meta tag'
    content = og.get_attribute('content')
    assert content and content.startswith('http'), (
        f'{filename} og:image is not an absolute URL: {content!r}'
    )


@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_no_js_errors(page: Page, filename: str):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(f'{BASE}/{filename}')
    try:
        page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass  # CDN assets may be slow in CI
    assert errors == [], f'JS errors on {filename}: {errors}'


@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_no_horizontal_scroll_mobile(page: Page, filename: str):
    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto(f'{BASE}/{filename}')
    scroll_width = page.evaluate('document.body.scrollWidth')
    viewport_width = page.evaluate('window.innerWidth')
    assert scroll_width <= viewport_width + 2, (
        f'{filename}: horizontal overflow on mobile '
        f'(scrollWidth={scroll_width} > viewportWidth={viewport_width})'
    )


def test_vitals_grid_no_overflow_mobile(page: Page):
    """Specifically ensure the vitals-grid on the flood page doesn't overflow its container."""
    page.set_viewport_size({'width': 360, 'height': 800}) # Slightly narrower than iPhone
    page.goto(f'{BASE}/flood_risk_gatineau_ottawa.html')
    
    overflow = page.evaluate("""
        () => {
            const grid = document.querySelector('.vitals-grid');
            if (!grid) return 'Grid not found';
            if (grid.scrollWidth > grid.clientWidth + 1) {
                return `scrollWidth ${grid.scrollWidth} > clientWidth ${grid.clientWidth}`;
            }
            return null;
        }
    """)
    assert overflow is None, f'Vitals grid overflow on mobile: {overflow}'



def test_flood_simulator_updates_multiple_stations(page: Page):
    """Verify that the offset slider updates both Britannia and Hull levels."""
    page.goto(f'{BASE}/flood_risk_gatineau_ottawa.html')
    
    # Get initial values
    initial_brit = page.locator('#levelDisplay').inner_text()
    initial_hull = page.locator('#hullDisplay').inner_text()
    
    # Move slider
    slider = page.locator('#levelSlider')
    page.evaluate("s => { s.value = '2.00'; s.dispatchEvent(new Event('input')); }", slider.element_handle())
    
    # Verify updates
    page.wait_for_timeout(300)
    new_brit = page.locator('#levelDisplay').inner_text()
    new_hull = page.locator('#hullDisplay').inner_text()
    
    assert float(new_brit) > float(initial_brit), f"Britannia level didn't increase: {initial_brit} -> {new_brit}"
    assert float(new_hull) > float(initial_hull), f"Hull level didn't increase: {initial_hull} -> {new_hull}"
    expect(page.locator('#offsetDisplay')).to_contain_text('2.00m')


@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_no_horizontal_scroll_desktop(page: Page, filename: str):
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/{filename}')
    try:
        page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass
    scroll_width = page.evaluate('document.body.scrollWidth')
    viewport_width = page.evaluate('window.innerWidth')
    assert scroll_width <= viewport_width + 2, (
        f'{filename}: horizontal overflow on desktop '
        f'(scrollWidth={scroll_width} > viewportWidth={viewport_width})'
    )



@pytest.mark.parametrize('filename', analysis_pages())
def test_analysis_page_no_vertical_clip_desktop(page: Page, filename: str):
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/{filename}')
    try:
        page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass
    clipped = page.evaluate("""
        () => {
            const canvases = document.querySelectorAll('canvas');
            for (const c of canvases) {
                const parent = c.parentElement;
                if (parent && c.offsetHeight > parent.offsetHeight + 5) {
                    return (c.id || 'canvas') + ': ' + c.offsetHeight + 'px > parent ' + parent.offsetHeight + 'px';
                }
            }
            return null;
        }
    """)
    assert clipped is None, f'{filename}: canvas overflows its container — {clipped}'


def test_canadian_dashboard_province_view_height_stabilizes(page: Page):
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/employment_rate_canada.html')
    try:
        page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass

    def assert_height_stable(toggle_selector: str):
        page.locator(toggle_selector).click()
        page.wait_for_timeout(250)
        heights = []
        for _ in range(5):
            heights.append(page.evaluate('document.documentElement.scrollHeight'))
            page.wait_for_timeout(200)
        assert max(heights) - min(heights) <= 4, (
            f'{toggle_selector}: page height keeps changing after switching to province view: {heights}'
        )

    assert_height_stable('#rate-btnS')
    page.locator('.tab', has_text='Government Debt').click()
    assert_height_stable('#debt-btnS')
    page.locator('.tab', has_text='Population').click()
    assert_height_stable('#pop-btnS')


def test_flood_dashboard_height_stabilizes(page: Page):
    """Ensure the flood dashboard height remains stable across all tabs."""
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/flood_risk_gatineau_ottawa.html')
    try:
        page.wait_for_load_state('networkidle', timeout=8000)
    except Exception:
        pass

    tabs = ['gauge', 'history', 'snowpack']
    for tab in tabs:
        page.evaluate(f"showTab('{tab}')")
        page.wait_for_timeout(300)
        heights = []
        for _ in range(5):
            heights.append(page.evaluate('document.documentElement.scrollHeight'))
            page.wait_for_timeout(200)
        
        diff = max(heights) - min(heights)
        assert diff <= 5, (
            f'Tab {tab}: page height is unstable (range: {min(heights)}-{max(heights)}): {heights}'
        )
        
        viewport_height = page.evaluate('window.innerHeight')
        assert max(heights) <= viewport_height + 50, (
            f'Tab {tab}: page height {max(heights)} exceeds viewport {viewport_height}'
        )


@pytest.mark.parametrize('filename', analysis_pages())
def test_viz_elements_have_height(page: Page, filename: str):
    """Ensure that critical visualization elements (canvases, maps) have a non-zero height when visible."""
    page.goto(f'{BASE}/{filename}')
    try:
        page.wait_for_load_state('networkidle', timeout=5000)
    except Exception:
        pass

    # Check multiple tabs if the page has a .tab interface
    tab_count = page.locator('.tab').count()
    if tab_count > 0:
        tabs = page.locator('.tab')
        for i in range(tab_count):
            # Click the tab and wait for animation/rendering
            tabs.nth(i).click()
            page.wait_for_timeout(300)
            
            elements = page.evaluate("""
                () => {
                    const results = [];
                    // Find the container that was just activated
                    const activePanel = document.querySelector('.panel.active');
                    const container = activePanel || document.body;
                    
                    const canvases = container.querySelectorAll('canvas');
                    const maps = container.querySelectorAll('#floodMap, .leaflet-container');
                    
                    canvases.forEach(c => {
                        // Element is only 'collapsed' if it's supposed to be visible (offsetParent is not null)
                        if (c.offsetParent !== null && c.offsetHeight < 10) {
                            results.push({ id: c.id || 'unnamed-canvas', h: c.offsetHeight });
                        }
                    });
                    maps.forEach(m => {
                        if (m.offsetParent !== null && m.offsetHeight < 10) {
                            results.push({ id: m.id || 'unnamed-map', h: m.offsetHeight });
                        }
                    });
                    return results;
                }
            """)
            tab_name = page.evaluate(f"document.querySelectorAll('.tab')[{i}].innerText").strip()
            assert not elements, f"Collapsed visualizations on {filename} tab '{tab_name}': {elements}"
    else:
        # Standard page with no tabs
        page.wait_for_timeout(500)
        elements = page.evaluate("""
            () => {
                const results = [];
                const canvases = document.querySelectorAll('canvas');
                canvases.forEach(c => {
                    if (c.offsetParent !== null && c.offsetHeight < 10) {
                        results.push({ id: c.id || 'unnamed-canvas', h: c.offsetHeight });
                    }
                });
                return results;
            }
        """)
        assert not elements, f"Collapsed visualizations on {filename}: {elements}"
