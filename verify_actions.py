import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Start local server to serve duckdb-wasm and files
        import subprocess
        import time
        server_process = subprocess.Popen(["python3", "-m", "http.server", "8765", "--bind", "127.0.0.1"])

        # Wait a bit for server to start
        time.sleep(2)

        try:
            await page.goto("http://127.0.0.1:8765/dropzone.html", wait_until="networkidle")

            # Wait for DuckDB to initialize by checking for load samples button
            await page.wait_for_selector("#load-samples", timeout=30000)

            # Wait a moment for UI to settle
            await page.wait_for_timeout(2000)

            # Assert buttons are disabled
            is_recipe_disabled = await page.locator("#query-recipes").is_disabled()
            is_export_disabled = await page.locator("#export-db").is_disabled()
            is_clear_disabled = await page.locator("#clear-data").is_disabled()

            assert is_recipe_disabled, "Recipe Select should be disabled initially"
            assert is_export_disabled, "Export DB button should be disabled initially"
            assert is_clear_disabled, "Clear Data button should be disabled initially"

            print("Successfully verified disabled state!")

            os.makedirs("/home/jules/verification", exist_ok=True)
            await page.screenshot(path="/home/jules/verification/disabled_buttons.png")

            # Click load samples
            await page.click("#load-samples")
            await page.wait_for_selector("#status:has-text('Loaded')", timeout=15000)

            # Wait a moment for UI to settle
            await page.wait_for_timeout(2000)

            # Assert buttons are enabled
            is_recipe_disabled = await page.locator("#query-recipes").is_disabled()
            is_export_disabled = await page.locator("#export-db").is_disabled()
            is_clear_disabled = await page.locator("#clear-data").is_disabled()

            assert not is_recipe_disabled, "Recipe Select should be enabled after load"
            assert not is_export_disabled, "Export DB button should be enabled after load"
            assert not is_clear_disabled, "Clear Data button should be enabled after load"

            print("Successfully verified enabled state!")
            await page.screenshot(path="/home/jules/verification/enabled_buttons.png")

        finally:
            server_process.terminate()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
