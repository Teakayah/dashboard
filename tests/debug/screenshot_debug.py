import pytest
from playwright.sync_api import Page

BASE = 'http://localhost:8765'

def test_screenshot_flood(page: Page):
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/flood_risk_gatineau_ottawa.html')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='flood_debug.png')
    
    page.goto(f'{BASE}/nhpi_big6_comparison.html')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='nhpi_debug.png')

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
