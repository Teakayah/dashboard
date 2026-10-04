from playwright.sync_api import Page, expect
from helpers import BASE
import re

def test_fullscreen_wraps_canvas(page: Page):
    """Canvases should be wrapped with a chart-container and a fullscreen button."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector('canvas')

    container = page.locator(".chart-container").first
    expect(container).to_be_visible()
    expect(container.locator("canvas").first).to_be_visible()

    btn = container.locator(".fullscreen-btn")
    expect(btn).to_be_visible()
    expect(btn).to_have_text("⛶")

def test_fullscreen_toggle_behavior(page: Page):
    """Clicking the fullscreen button toggles classes and body overflow."""
    page.goto(f"{BASE}/nhpi_big6_comparison.html", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector('canvas')

    container = page.locator(".chart-container").first
    btn = container.locator(".fullscreen-btn")

    btn.click()
    expect(container).to_have_class(re.compile(r"chart-fullscreen"))
    expect(btn).to_have_text("✕")
    expect(page.locator("body")).to_have_css("overflow", "hidden")

    btn.click()
    expect(container).not_to_have_class(re.compile(r"chart-fullscreen"))
    expect(btn).to_have_text("⛶")
    expect(page.locator("body")).to_have_css("overflow", "visible")

def test_fullscreen_mutation_observer(page: Page):
    """Dynamically added canvases should automatically be wrapped."""
    page.goto(f"{BASE}/dropzone.html", wait_until="domcontentloaded", timeout=60000)

    page.evaluate('''() => {
        const c = document.createElement('canvas');
        c.id = 'dynamic-canvas';
        document.body.appendChild(c);
    }''')

    dynamic_canvas = page.locator("#dynamic-canvas")
    page.wait_for_selector("#dynamic-canvas")

    container = dynamic_canvas.locator("..")
    expect(container).to_have_class("chart-container")
    expect(container.locator(".fullscreen-btn")).to_be_visible()
