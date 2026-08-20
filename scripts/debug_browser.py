import os
import sys
import threading
from http.server import HTTPServer

from playwright.sync_api import sync_playwright

# Add root folder to path so we can import conftest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tests.conftest import PORT, WasmHandler


def run_server():
    server = HTTPServer(('127.0.0.1', PORT), WasmHandler)
    server.serve_forever()

def main():
    # Start server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Local server started on port", PORT)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Block service workers to have a clean slate as in conftest.py
        context = browser.new_context(service_workers='block')
        page = context.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"CONSOLE: [{msg.type}] {msg.text}"))
        # Capture page errors
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))

        print("Navigating to dropzone.html...")
        page.goto(f"http://localhost:{PORT}/dropzone.html")

        # Wait for some time to see what happens
        print("Waiting for 10 seconds for initialization...")
        page.wait_for_timeout(10000)

        status = page.locator("#status").inner_text()
        print(f"Final status: {status}")

        browser.close()

if __name__ == "__main__":
    main()
