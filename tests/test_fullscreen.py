import re
from playwright.sync_api import Page, expect
from helpers import BASE


def test_fullscreen_injection_and_toggle_state(page: Page):
    """Verify that fullscreen button is injected, toggles fullscreen classes and body overflow."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded", timeout=60000)

    btn = page.locator(".fullscreen-btn").first
    expect(btn).to_be_visible(timeout=10000)
    expect(btn).to_have_text("⛶")
    expect(btn).to_have_attribute("aria-label", "Enter Full Screen")

    container = btn.locator("..")
    expect(container).to_have_class(re.compile(r"chart-container"))
    expect(container).not_to_have_class(re.compile(r"chart-fullscreen"))
    expect(btn).to_have_attribute("title", "Full Screen")
    assert page.evaluate("document.body.style.overflow") != "hidden"

    # Click to enter fullscreen
    btn.click()
    expect(container).to_have_class(re.compile(r"chart-fullscreen"))
    expect(btn).to_have_text("✕")
    expect(btn).to_have_attribute("aria-label", "Exit Full Screen")
    expect(btn).to_have_attribute("title", "Exit Full Screen")
    assert page.evaluate("document.body.style.overflow") == "hidden"

    # Click to exit fullscreen
    btn.click()
    expect(container).not_to_have_class(re.compile(r"chart-fullscreen"))
    expect(btn).to_have_text("⛶")
    expect(btn).to_have_attribute("aria-label", "Enter Full Screen")
    expect(btn).to_have_attribute("title", "Full Screen")
    assert page.evaluate("document.body.style.overflow") != "hidden"


def test_fullscreen_dispatches_resize_event(page: Page):
    """Verify that toggling fullscreen dispatches a resize event to the window for Chart.js."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded", timeout=60000)

    btn = page.locator(".fullscreen-btn").first
    expect(btn).to_be_visible(timeout=10000)

    page.evaluate("""
        window.__resizeCount = 0;
        window.addEventListener('resize', () => { window.__resizeCount++; });
    """)

    btn.click()
    assert page.evaluate("window.__resizeCount") == 1

    btn.click()
    assert page.evaluate("window.__resizeCount") == 2


def test_fullscreen_mutation_observer_wraps_dynamic_canvas(page: Page):
    """Verify that dynamically added canvas elements are automatically wrapped by MutationObserver."""
    page.goto(f"{BASE}/dropzone.html", wait_until="domcontentloaded", timeout=60000)

    page.evaluate("""
        () => {
            const canvas = document.createElement('canvas');
            canvas.id = 'dynamic-canvas';
            document.body.appendChild(canvas);
        }
    """)

    dynamic_btn = page.locator("#dynamic-canvas").locator("..").locator(".fullscreen-btn")
    expect(dynamic_btn).to_be_visible(timeout=5000)
    expect(dynamic_btn).to_have_text("⛶")
