from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:3000/dropzone.html')
    time.sleep(1)
    page.click('#clear-data')
    try:
        page.on('dialog', lambda dialog: dialog.accept())
    except:
        pass
    time.sleep(1)
    page.click('#load-samples')
    page.wait_for_selector('#schema-display:has-text("departments")')
    print(page.locator('#schema-display').inner_text())
    browser.close()
