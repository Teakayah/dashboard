from playwright.sync_api import Page, expect
from helpers import BASE
import re

def test_fullscreen_button_injected_and_toggles(page: Page):
    page.goto(f'{BASE}/nhpi_big6_comparison.html', wait_until='domcontentloaded', timeout=60000)

    # Wait for at least one fullscreen button to be injected
    btn = page.locator('.fullscreen-btn').first
    expect(btn).to_be_visible(timeout=10000)
    expect(btn).to_have_text('⛶')
    expect(btn).to_have_attribute('aria-label', 'Enter Full Screen')

    container = btn.locator('..')
    expect(container).to_have_class(re.compile(r'chart-container'))

    # Click to enter fullscreen
    btn.click()
    expect(container).to_have_class(re.compile(r'chart-fullscreen'))
    expect(btn).to_have_text('✕')
    expect(btn).to_have_attribute('aria-label', 'Exit Full Screen')

    # Verify body overflow is hidden
    overflow = page.evaluate('document.body.style.overflow')
    assert overflow == 'hidden'

    # Click to exit fullscreen
    btn.click()
    expect(container).not_to_have_class(re.compile(r'chart-fullscreen'))
    expect(btn).to_have_text('⛶')
    expect(btn).to_have_attribute('aria-label', 'Enter Full Screen')

    # Verify body overflow is restored
    overflow = page.evaluate('document.body.style.overflow')
    assert overflow == ''

def test_fullscreen_mutation_observer_wraps_dynamic_canvas(page: Page):
    page.goto(f'{BASE}/nhpi_big6_comparison.html', wait_until='domcontentloaded', timeout=60000)

    # Inject a dynamic canvas
    page.evaluate('''() => {
        const canvas = document.createElement('canvas');
        canvas.id = 'dynamic-canvas';
        document.body.appendChild(canvas);
    }''')

    # Observer should wrap it
    dynamic_btn = page.locator('#dynamic-canvas').locator('..').locator('.fullscreen-btn')
    expect(dynamic_btn).to_be_visible(timeout=5000)
