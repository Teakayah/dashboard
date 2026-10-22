from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:3000/test_batch.html')
    page.wait_for_function('document.body.innerHTML.includes("Success!") || document.body.innerHTML.includes("Error:")')
    print(page.content())
    browser.close()
