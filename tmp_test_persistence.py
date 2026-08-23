from playwright.sync_api import sync_playwright
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto('http://localhost:8765/dropzone.html', wait_until='domcontentloaded')
        page.wait_for_function(
            "() => { const t = document.getElementById('status')?.textContent ?? ''; return t === 'DuckDB Ready' || t.startsWith('Restored'); }",
            timeout=90000
        )
        page.locator('#load-samples').click()
        page.wait_for_function(
            "document.getElementById('schema-display').textContent.includes('employees')",
            timeout=15000,
        )
        page.reload(wait_until='domcontentloaded')
        try:
            page.wait_for_function(
                "() => { const t = document.getElementById('status')?.textContent ?? ''; return t.startsWith('Restored'); }",
                timeout=15000
            )
            print("Successfully found Restored")
        except Exception as e:
            print("Failed to find Restored:", e)
            print("Status is:", page.locator('#status').inner_text())
            print("Schema is:", page.locator('#schema-display').inner_text())
            print("Wait for DuckDB Ready then check schema:")
            page.wait_for_function(
                "() => { const t = document.getElementById('status')?.textContent ?? ''; return t === 'DuckDB Ready' || t.startsWith('Restored'); }",
                timeout=90000
            )
            print("Status is:", page.locator('#status').inner_text())
            print("Schema is:", page.locator('#schema-display').inner_text())
        browser.close()
if __name__ == '__main__':
    main()
