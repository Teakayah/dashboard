import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PORT = 8765
BASE_URL = f'http://localhost:{PORT}'


@pytest.fixture(scope='session', autouse=True)
def local_server():
    """Serve the repo root over HTTP for the duration of the test session."""
    proc = subprocess.Popen(
        ['python3', '-m', 'http.server', str(PORT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    yield proc
    proc.terminate()
    proc.wait()


def pytest_configure(config):
    config.addinivalue_line('markers', 'mobile: mark test as a mobile-viewport test')
