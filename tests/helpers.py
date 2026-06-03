"""Shared constants and helpers for Playwright test files."""

from playwright.sync_api import Page

BASE = 'http://localhost:8765'
DROPZONE_URL = f'{BASE}/dropzone.html'
DUCKDB_READY_TIMEOUT = 90_000
ACTION_TIMEOUT = 15_000


def wait_for_duckdb_ready(page: Page) -> None:
    page.wait_for_function(
        """() => {
            const t = document.getElementById('status')?.textContent ?? '';
            return t === 'DuckDB Ready' || t.startsWith('Restored');
        }""",
        timeout=DUCKDB_READY_TIMEOUT,
    )


def load_samples(page: Page) -> None:
    page.locator('#load-samples').click()
    page.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )
