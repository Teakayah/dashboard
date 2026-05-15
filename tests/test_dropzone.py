"""
Front-end integration tests for the Analytical Drop-Zone (DuckDB-Wasm).

Requires the local HTTP server started automatically by conftest.py (port 8765).
Run with:  pytest tests/test_dropzone.py -v
"""

from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, expect

DROPZONE = 'http://localhost:8765/dropzone.html'
READY_TIMEOUT = 20_000   # ms — generous headroom under our 30 s app timeout
ACTION_TIMEOUT = 10_000  # ms — for post-init interactions


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def dz(browser: Browser) -> Page:
    """Fresh browser context per test — clean IndexedDB, no stale SW cache."""
    ctx = browser.new_context(service_workers='block')
    pg = ctx.new_page()
    yield pg
    ctx.close()


# ── Shared helper ─────────────────────────────────────────────────────────────

def _wait_for_ready(page: Page) -> None:
    """Block until DuckDB is initialised or prior session is restored."""
    page.wait_for_function(
        """() => {
            const t = document.getElementById('status')?.textContent ?? '';
            return t === 'DuckDB Ready' || t.startsWith('Restored');
        }""",
        timeout=READY_TIMEOUT,
    )


# ── Initialisation ────────────────────────────────────────────────────────────

def test_duckdb_init_reaches_ready(dz: Page):
    """#status must reach 'DuckDB Ready' — the core P0 regression guard."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    status = dz.locator('#status').inner_text()
    assert 'Error' not in status, f'Init failed: {status}'
    assert 'timed out' not in status.lower(), f'Init timed out: {status}'


def test_no_js_errors_on_load(dz: Page):
    errors: list[str] = []
    dz.on('pageerror', lambda e: errors.append(str(e)))
    dz.goto(DROPZONE)
    _wait_for_ready(dz)
    assert errors == [], f'JS errors during DuckDB init: {errors}'


# ── Sample data ───────────────────────────────────────────────────────────────

def test_load_samples_creates_both_tables(dz: Page):
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('status').textContent.includes('table')",
        timeout=ACTION_TIMEOUT,
    )

    schema = dz.locator('#schema-display')
    expect(schema).to_contain_text('employees')
    expect(schema).to_contain_text('departments')


def test_load_samples_populates_sql_input(dz: Page):
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    sql = dz.locator('#sql-input').input_value()
    assert 'employees' in sql.lower(), f'SQL input not pre-populated: {sql!r}'


# ── CSV file load ─────────────────────────────────────────────────────────────

def test_csv_file_loads_and_shows_schema(dz: Page, tmp_path: Path):
    csv = tmp_path / 'sales_data.csv'
    csv.write_text('id,product,revenue\n1,Widget,100\n2,Gadget,200\n3,Doohickey,50\n')

    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#file-input').set_input_files(str(csv))
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.trim() !== ''",
        timeout=ACTION_TIMEOUT,
    )

    expect(dz.locator('#schema-display')).to_contain_text('sales_data')
    status = dz.locator('#status').inner_text()
    assert 'table' in status.lower(), f'Status after file load: {status!r}'


# ── Clear data ────────────────────────────────────────────────────────────────

def test_clear_data_wipes_schema(dz: Page):
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    dz.on('dialog', lambda dlg: dlg.accept())
    dz.locator('#clear-data').click()
    dz.wait_for_function(
        "document.getElementById('status').textContent === 'Storage cleared'",
        timeout=ACTION_TIMEOUT,
    )

    expect(dz.locator('#schema-display')).to_have_text('')


# ── Persistence ───────────────────────────────────────────────────────────────

def test_persistence_across_reload(dz: Page):
    """Tables loaded in one session must survive a full page reload."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    dz.reload()
    # After reload DuckDB re-opens the indexeddb:// database and calls restoreState()
    dz.wait_for_function(
        "document.getElementById('status').textContent.startsWith('Restored')",
        timeout=READY_TIMEOUT,
    )

    expect(dz.locator('#schema-display')).to_contain_text('employees')
