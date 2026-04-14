import socket
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PORT = 8765
BASE_URL = f'http://localhost:{PORT}'


def _wait_for_server(host: str, port: int, retries: int = 40, interval: float = 0.1) -> None:
    """Poll until the server accepts connections or raise after timeout."""
    for _ in range(retries):
        try:
            socket.create_connection((host, port), timeout=0.5).close()
            return
        except OSError:
            time.sleep(interval)
    raise RuntimeError(f'HTTP server did not start on {host}:{port}')


@pytest.fixture(scope='session', autouse=True)
def local_server():
    """Serve the repo root over HTTP for the duration of the test session."""
    proc = subprocess.Popen(
        ['python3', '-m', 'http.server', str(PORT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_server('localhost', PORT)
    yield proc
    proc.terminate()
    proc.wait()


def pytest_configure(config):
    config.addinivalue_line('markers', 'mobile: mark test as a mobile-viewport test')
