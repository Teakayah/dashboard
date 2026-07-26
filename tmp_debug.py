import pytest
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using OPFS requires a persistent context or allowing it?
        # Let's try regular context
        context = browser.new_context()
        page = context.new_page()
        page.goto('http://localhost:8765/dropzone.html')
        page.wait_for_function(
            "() => { const t = document.getElementById('status')?.textContent ?? ''; return t === 'DuckDB Ready' || t.startsWith('Restored'); }"
        )
        page.locator('#load-samples').click()
        page.wait_for_function(
            "document.getElementById('schema-display').textContent.includes('employees')"
        )

        # Test opfs support
        opfs_supported = page.evaluate("!!(navigator.storage && navigator.storage.getDirectory)")
        print("OPFS Supported in this context?", opfs_supported)

        page.reload()
        page.wait_for_function(
            "() => { const t = document.getElementById('status')?.textContent ?? ''; return t === 'DuckDB Ready' || t.startsWith('Restored'); }",
            timeout=90000
        )
        print("After reload status:", page.locator('#status').inner_text())
        browser.close()

if __name__ == '__main__':
    main()
