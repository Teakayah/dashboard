from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:3000/test_batch2.html')
    time.sleep(3)
    print(page.content())
    browser.close()
