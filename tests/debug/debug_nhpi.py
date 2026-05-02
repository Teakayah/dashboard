import pytest
from playwright.sync_api import Page

BASE = 'http://localhost:8765'

def test_debug_nhpi(page: Page):
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.goto(f'{BASE}/nhpi_big6_comparison.html')
    page.wait_for_load_state('networkidle')
    
    heights = page.evaluate("""
        () => {
            const h1 = document.querySelector('h1').offsetHeight;
            const subtitle = document.querySelector('.subtitle').offsetHeight;
            const app = document.querySelector('#app').offsetHeight;
            const cards = Array.from(document.querySelectorAll('.card')).map(c => c.offsetHeight);
            const canvases = Array.from(document.querySelectorAll('canvas')).map(c => c.offsetHeight);
            const wrappers = Array.from(document.querySelectorAll('.chart-wrap, .chart-sm')).map(c => c.offsetHeight);
            return { h1, subtitle, app, cards, canvases, wrappers, scrollHeight: document.documentElement.scrollHeight };
        }
    """)
    print("NHPI Debug:", heights)

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
