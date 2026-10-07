import re
from playwright.sync_api import Page, expect
from helpers import BASE

def test_fullscreen_button_toggles_fullscreen_state(page: Page):
    """Verify that clicking the fullscreen button toggles the chart-fullscreen class and body overflow."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded")

    # Wait for the fullscreen button to be injected by assets/fullscreen.js
    btn = page.locator('.fullscreen-btn').first
    expect(btn).to_be_visible()

    container = page.locator('.chart-container').first

    # Initially not fullscreen
    expect(container).not_to_have_class(re.compile(r'\bchart-fullscreen\b'))
    assert page.evaluate("document.body.style.overflow") != "hidden"
    expect(btn).to_have_text("⛶")
    expect(btn).to_have_attribute("aria-label", "Enter Full Screen")

    # Click to enter fullscreen
    btn.click()
    expect(container).to_have_class(re.compile(r'\bchart-fullscreen\b'))
    assert page.evaluate("document.body.style.overflow") == "hidden"
    expect(btn).to_have_text("✕")
    expect(btn).to_have_attribute("aria-label", "Exit Full Screen")

    # Click to exit fullscreen
    btn.click()
    expect(container).not_to_have_class(re.compile(r'\bchart-fullscreen\b'))
    assert page.evaluate("document.body.style.overflow") != "hidden"
    expect(btn).to_have_text("⛶")
    expect(btn).to_have_attribute("aria-label", "Enter Full Screen")

def test_fullscreen_button_dispatches_resize_event(page: Page):
    """Verify that clicking the fullscreen button dispatches a resize event to the window."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded")

    # Wait for the fullscreen button to be injected by assets/fullscreen.js
    btn = page.locator('.fullscreen-btn').first
    expect(btn).to_be_visible()

    # Attach a listener to the window object to count resize events
    page.evaluate("""
        window.resizeCount = 0;
        window.addEventListener('resize', () => { window.resizeCount++; });
    """)

    # Click to enter fullscreen
    btn.click()

    # Check that resize event was dispatched
    assert page.evaluate("window.resizeCount") == 1

    # Click to exit fullscreen
    btn.click()

    # Check that resize event was dispatched again
    assert page.evaluate("window.resizeCount") == 2
