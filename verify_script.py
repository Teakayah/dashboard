import asyncio
import os
from playwright.async_api import async_playwright
import subprocess

async def main():
    # Start local server to avoid CORS/Worker issues
    server = subprocess.Popen(["python3", "-m", "http.server", "8765", "--bind", "127.0.0.1"])
    await asyncio.sleep(2)

    os.makedirs("/home/jules/verification", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(record_video_dir="/home/jules/verification/")
        page = await context.new_page()

        await page.goto("http://127.0.0.1:8765/dropzone.html")

        # Focus share button to trigger focus-visible
        await page.locator("#share-btn").focus()
        await page.wait_for_timeout(500)
        await page.screenshot(path="/home/jules/verification/share_btn_focus.png")

        # Load samples to see schema columns
        await page.locator("#load-samples").click()
        await page.wait_for_timeout(5000) # wait for data and duckdb

        # Hover on a clickable column
        col_locator = page.locator(".clickable-col").first
        await col_locator.hover()
        await page.wait_for_timeout(500)
        await page.screenshot(path="/home/jules/verification/clickable_col_hover.png")

        await context.close()
        await browser.close()

    server.terminate()

if __name__ == "__main__":
    asyncio.run(main())
