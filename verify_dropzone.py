import os
import glob
from playwright.sync_api import sync_playwright, expect

os.makedirs("/home/jules/verification/videos", exist_ok=True)
os.makedirs("/home/jules/verification/screenshots", exist_ok=True)

def run_cuj(page, context):
    page.goto("http://localhost:8765/dropzone.html", wait_until="networkidle")
    page.wait_for_timeout(1000)

    # 1. Load samples (this one doesn't have the new toast but takes time)
    page.get_by_role("button", name="Load Sample Datasets").click()
    page.wait_for_timeout(3000)

    # Type a query
    page.locator("#sql-input").fill('SELECT * FROM "departments" LIMIT 10')
    page.wait_for_timeout(500)

    # Run query
    page.get_by_role("button", name="Run Query").click()
    page.wait_for_timeout(1500)

    # 2. Copy JSON
    page.get_by_role("button", name="Copy JSON").click()
    expect(page.get_by_role("alert").filter(has_text="JSON copied to clipboard")).to_be_visible()
    page.wait_for_timeout(1000)

    # 3. Download CSV
    with page.expect_download():
        page.get_by_role("button", name="Download Results as CSV").click()
    expect(page.get_by_role("alert").filter(has_text="CSV downloaded successfully")).to_be_visible()
    page.wait_for_timeout(1000)

    # 4. Export DB
    with page.expect_download():
        page.get_by_role("button", name="Export Database (.db)").click()
    expect(page.get_by_role("alert").filter(has_text="Database exported successfully")).to_be_visible()

    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
    page.wait_for_timeout(2000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Grant clipboard permissions for Copy JSON
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            permissions=['clipboard-read', 'clipboard-write']
        )
        page = context.new_page()
        try:
            run_cuj(page, context)
        finally:
            context.close()
            browser.close()
