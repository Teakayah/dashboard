import os
import time
from playwright.sync_api import sync_playwright

def verify():
    os.makedirs("/home/jules/verification", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(record_video_dir="/home/jules/verification/")
        page.goto("http://127.0.0.1:8765/dropzone.html")

        # Run first query
        page.fill("#sql-input", "SELECT 1 AS test")
        # Give enough time for the init DuckDB process
        page.wait_for_selector("#status:has-text('Ready')", state="visible", timeout=60000)
        page.click("#run-query")
        # In gridjs, the table wrapper has class .gridjs
        page.wait_for_selector(".gridjs", state="visible")
        time.sleep(1) # wait for grid render

        # Run second query to trigger updateConfig
        page.fill("#sql-input", "SELECT 2 AS test")
        page.click("#run-query")
        page.wait_for_selector(".gridjs", state="visible")
        time.sleep(1) # wait for grid render

        # Clear data to trigger destroy
        page.on("dialog", lambda dialog: dialog.accept())
        page.click("#clear-data")
        time.sleep(1) # wait for clear operation

        page.screenshot(path="/home/jules/verification/screenshot.png")
        browser.close()

if __name__ == "__main__":
    verify()
