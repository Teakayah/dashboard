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
    link = page.locator('footer a')
    expect(link).to_be_visible()
    href = link.get_attribute('href')
    assert href and 'github.com' in href


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
