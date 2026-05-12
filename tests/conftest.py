from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

import pytest

REPO_ROOT = Path(__file__).parent.parent
PORT = 8765


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


@pytest.fixture(scope='session', autouse=True)
def local_server():
    """Serve the repo root over HTTP for the duration of the test session."""
    server = HTTPServer(('localhost', PORT), WasmHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def pytest_configure(config):
    config.addinivalue_line('markers', 'mobile: mark test as a mobile-viewport test')
