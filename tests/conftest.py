from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import subprocess
import threading

import pytest
from playwright.sync_api import Browser, Page

REPO_ROOT = Path(__file__).parent.parent
PORT = 8765
BASE_URL = f'http://localhost:{PORT}'


class WasmHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def end_headers(self):
        # Allow Cross-Origin Isolation for SharedArrayBuffer if needed
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


WasmHandler.extensions_map.update({
    ".wasm": "application/wasm",
    ".js": "application/javascript",
    ".mjs": "application/javascript",
})


def _ensure_test_pages_hydrated() -> None:
    """Ensure required analysis and index pages exist for local testing, hydrating from git if missing."""
    pages = [
        'employment_rate_canada.html',
        'nhpi_big6_comparison.html',
        'flood_risk_gatineau_ottawa.html',
        'index.html',
    ]
    for page in pages:
        target = REPO_ROOT / page
        if not target.exists():
            for ref in ['origin/main', 'main', 'HEAD']:
                try:
                    content = subprocess.check_output(
                        ['git', 'show', f'{ref}:{page}'],
                        stderr=subprocess.DEVNULL,
                    )
                    target.write_bytes(content)
                    break
                except Exception:
                    continue


@pytest.fixture()
def dz(browser: Browser) -> Page:
    """Fresh browser context for Drop-Zone tests — clean IndexedDB, no stale SW."""
    ctx = browser.new_context(
        service_workers='block',
        permissions=['clipboard-read', 'clipboard-write'],
    )
    pg = ctx.new_page()
    yield pg
    ctx.close()

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "bypass_csp": True,
    }


def pytest_configure(config):
    config.addinivalue_line('markers', 'mobile: mark test as a mobile-viewport test')
    if not hasattr(config, "workerinput"):
        # We are the master node (or not using xdist)
        _ensure_test_pages_hydrated()
        server = ThreadingHTTPServer(('127.0.0.1', PORT), WasmHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config._local_server = server

def pytest_unconfigure(config):
    server = getattr(config, "_local_server", None)
    if server is not None:
        server.shutdown()
        server.server_close()
