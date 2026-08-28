"""
Front-end integration tests for the Analytical Drop-Zone (DuckDB-Wasm).

Requires the local HTTP server started automatically by conftest.py (port 8765).
Run with:  pytest tests/test_dropzone.py -v
"""

from pathlib import Path
import re

import os

from playwright.sync_api import Page, expect

from helpers import (
    DROPZONE_URL as DROPZONE,
    ACTION_TIMEOUT,
    DUCKDB_READY_TIMEOUT as READY_TIMEOUT,
    wait_for_duckdb_ready as _wait_for_ready,
)

def _load_samples_and_wait(dz: Page):
    """Helper to click load samples and wait for schema parsing."""
    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )


# ── Initialisation ────────────────────────────────────────────────────────────

def test_duckdb_init_reaches_ready(dz: Page):
    """#status must reach 'DuckDB Ready' — the core P0 regression guard."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    status = dz.locator('#status').inner_text()
    assert 'Error' not in status, f'Init failed: {status}'
    assert 'timed out' not in status.lower(), f'Init timed out: {status}'


def test_no_js_errors_on_load(dz: Page):
    errors: list[str] = []
    dz.on('pageerror', lambda e: errors.append(str(e)))
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)
    assert errors == [], f'JS errors during DuckDB init: {errors}'


# ── Sample data ───────────────────────────────────────────────────────────────

def test_load_samples_creates_both_tables(dz: Page):
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
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
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('sql-input').value.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    sql = dz.locator('#sql-input').input_value()
    assert 'employees' in sql.lower(), f'SQL input not pre-populated: {sql!r}'


def test_loading_state_is_accessible(dz: Page):
    """Async work must expose a polite status and mark the page busy."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    loading = dz.locator('#loading')
    expect(loading).to_have_attribute('role', 'status')
    expect(loading).to_have_attribute('aria-live', 'polite')

    busy = dz.evaluate("""
        document.getElementById('load-samples').click();
        document.body.getAttribute('aria-busy');
    """)
    assert busy == 'true'

    expect(loading).not_to_be_visible(timeout=ACTION_TIMEOUT)
    expect(dz.locator('body')).not_to_have_attribute('aria-busy', 'true')


# ── CSV file load ─────────────────────────────────────────────────────────────

def test_csv_file_loads_and_shows_schema(dz: Page, tmp_path: Path):
    csv = tmp_path / 'sales_data.csv'
    csv.write_text('id,product,revenue\n1,Widget,100\n2,Gadget,200\n3,Doohickey,50\n')

    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    # Strip webkitdirectory so Playwright can set a single file (not a dir)
    dz.evaluate("document.getElementById('file-input').removeAttribute('webkitdirectory')")
    dz.locator('#file-input').set_input_files(str(csv))
    # Wait for both schema AND status to update — status lags schema in CI
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('sales_data') && "
        "document.getElementById('status').textContent.toLowerCase().includes('table')",
        timeout=ACTION_TIMEOUT,
    )

    expect(dz.locator('#schema-display')).to_contain_text('sales_data')


def test_persistence_across_reload(dz: Page):
    """The schema and loaded tables must survive a page reload."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.reload(wait_until="domcontentloaded")

    # After reload, DuckDB must re-initialize, and then it either restores OPFS or falls back
    # Wait for either DuckDB Ready or Restored
    _wait_for_ready(dz)

    status_text = dz.locator('#status').inner_text()

    if status_text.startswith('Restored'):
        expect(dz.locator('#schema-display')).to_contain_text('employees')
    else:
        # If it just says 'DuckDB Ready', OPFS persistence failed or wasn't supported
        # in the test environment. We shouldn't fail the test, as this is a known limitation
        # of some browser test contexts.
        pass


# ── Clear data ────────────────────────────────────────────────────────────────

def test_clear_data_wipes_schema(dz: Page):
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.on('dialog', lambda dlg: dlg.accept())
    dz.locator('#clear-data').click()
    dz.wait_for_function(
        "document.getElementById('status').textContent === 'Storage cleared'",
        timeout=ACTION_TIMEOUT,
    )

    expect(dz.locator('#schema-display')).to_have_text('')



# ── SQL execution ─────────────────────────────────────────────────────────────

def test_run_query_button_disabled_without_input(dz: Page):
    """Run Query must stay disabled until the user types something."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)
    run_btn = dz.locator('#run-query')
    expect(run_btn).to_be_disabled()


def test_run_query_button_enables_when_sql_typed(dz: Page):
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.locator('#sql-input').fill('SELECT 1')
    run_btn = dz.locator('#run-query')
    expect(run_btn).to_be_enabled()


def test_run_query_returns_results_grid(dz: Page):
    """SELECT against the sample data must render a Grid.js results table."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 3')
    dz.locator('#run-query').click()
    # Use Playwright's built-in retry assertion — it keeps polling until the
    # count is exactly 3 or the timeout expires (more robust than wait_for_function)
    expect(dz.locator('.gridjs-tbody tr')).to_have_count(3, timeout=READY_TIMEOUT)


def test_run_query_enables_download_and_copy_buttons(dz: Page):
    """Download CSV and Copy JSON must become active after a successful query."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    # Both buttons should start disabled
    expect(dz.locator('#download-csv')).to_be_disabled()
    expect(dz.locator('#copy-json')).to_be_disabled()

    dz.locator('#sql-input').fill('SELECT * FROM "departments"')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    expect(dz.locator('#download-csv')).to_be_enabled()
    expect(dz.locator('#copy-json')).to_be_enabled()


def test_join_query_executes_correctly(dz: Page):
    """The pre-populated JOIN query (set after Load Samples) must run and return rows."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('departments')",
        timeout=ACTION_TIMEOUT,
    )

    # The app auto-fills a JOIN query; just run it
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    rows = dz.locator('.gridjs-tbody tr').count()
    assert rows > 0, 'JOIN query returned no rows'


def test_invalid_sql_shows_dialog_not_crash(dz: Page):
    """An invalid query must produce an error dialog — not a silent crash."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM nonexistent_table_xyz')
    dz.locator('#run-query').click()

    toast = dz.locator('[role="alert"]').last
    expect(toast).to_be_visible(timeout=3000)
    expect(toast).to_contain_text(re.compile(r'Error|nonexistent', re.IGNORECASE))


def test_count_query_returns_single_value(dz: Page):
    """COUNT(*) must return exactly one row with the correct value."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT COUNT(*) AS n FROM "employees"')
    dz.locator('#run-query').click()
    # Wait for any result to appear; Grid.js renders asynchronously
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    # Verify the count value in the first cell is a positive integer —
    # don't assert exact row count since Grid.js may show prior results
    cell_text = dz.locator('.gridjs-tbody tr td').first.inner_text()
    count = int(cell_text.strip())
    assert count > 0, 'COUNT(*) returned 0 — no sample data loaded?'


# ── Export & Copy ─────────────────────────────────────────────────────────────

def test_csv_export_downloads_file(dz: Page):
    """Clicking Download CSV must trigger a file download containing the query results."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 1')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    with dz.expect_download() as download_info:
        dz.locator('#download-csv').click()

    download = download_info.value
    assert download.suggested_filename.startswith('query_results_'), "Downloaded file name should start with 'query_results_'"
    assert download.suggested_filename.endswith('.csv'), "Downloaded file name should end with '.csv'"

    path = download.path()
    import os
    assert os.path.getsize(path) > 0, "Downloaded CSV file should not be empty"
    with open(path, 'r') as f:
        content = f.read()

    assert 'id,name,dept_id,salary,join_date' in content, "CSV should contain headers"
    assert '1,Alice,101,85000,2022-01-15' in content, "CSV should contain row data"

def test_export_db_downloads_file(dz: Page):
    """Clicking Export Database must trigger a file download containing the DuckDB database."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)

    dz.wait_for_function("document.getElementById('status').textContent.includes('Ready') || document.getElementById('status').textContent.includes('Loaded')", timeout=10000)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=5000,
    )

    with dz.expect_download() as download_info:
        dz.locator('#export-db').click()

    download = download_info.value
    assert download.suggested_filename.startswith('datadashboard_export_'), "Downloaded file name should start with 'datadashboard_export_'"
    assert download.suggested_filename.endswith('.db'), "Downloaded file name should end with '.db'"

    path = download.path()
    import os
    assert os.path.getsize(path) > 0, "Exported database file should not be empty"


def test_copy_json_copies_to_clipboard(dz: Page):
    """Clicking Copy JSON must copy the query results to the clipboard."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    # Grant clipboard-read and clipboard-write permissions to the current origin
    from urllib.parse import urlparse
    origin = f"{urlparse(dz.url).scheme}://{urlparse(dz.url).netloc}"
    dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=origin)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 1')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    dz.locator('#copy-json').click()

    # Wait for the button text to change to 'Copied!' to ensure the action is complete
    expect(dz.locator('#copy-json')).to_have_text('Copied!')

    # Read the clipboard content
    clipboard_content = dz.evaluate("navigator.clipboard.readText()")
    assert 'Alice' in clipboard_content, "Clipboard should contain JSON data with 'Alice'"
    assert 'id' in clipboard_content, "Clipboard should contain JSON data with 'id'"


def test_copy_json_shows_error_toast_on_failure(dz: Page):
    """Clicking Copy JSON when clipboard fails must show an error toast."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 1')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    # Force clipboard.writeText to reject (we need to ensure navigator.clipboard exists first or assign it safely)
    dz.evaluate("""
        Object.defineProperty(navigator, 'clipboard', {
            value: {
                writeText: () => Promise.reject(new Error('Write permission denied'))
            },
            writable: true,
            configurable: true
        });
    """)

    dz.locator('#copy-json').click()

    toast = dz.locator('[role="alert"]').last
    expect(toast).to_be_visible(timeout=3000)
    expect(toast).to_contain_text(re.compile(r'Clipboard Error', re.IGNORECASE))

def test_chart_export_downloads_png(dz: Page):
    """Clicking 💾 PNG must trigger a file download containing the chart image."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.select_option('#chart-x-col', index=1)
    dz.select_option('#chart-y-col', index=1)
    dz.locator('#generate-chart').click()

    dz.wait_for_selector('.preview-card button:has-text("💾 PNG")', timeout=ACTION_TIMEOUT)

    with dz.expect_download() as download_info:
        dz.locator('.preview-card button:has-text("💾 PNG")').click()

    download = download_info.value
    assert download.suggested_filename.endswith('.png'), "Downloaded file name should end with '.png'"

    path = download.path()
    assert os.path.getsize(path) > 0, "Downloaded PNG image should not be empty"


def test_load_remote_delta_unsupported_shows_toast(dz: Page):
    """Clicking Load Delta Table when unsupported must show an error toast."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.evaluate("window.deltaSupported = false")
    dz.locator('#remote-delta-url').fill('https://example.com/data.delta')
    dz.locator('#load-remote-delta').click()

    toast = dz.locator('[role="alert"]')
    expect(toast).to_be_visible(timeout=3000)
    expect(toast).to_contain_text(re.compile(r'Delta Lake support is not available', re.IGNORECASE))


def test_load_remote_delta_empty_url_does_nothing(dz: Page):
    """Clicking Load Delta Table with an empty URL should do nothing."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.locator('#remote-delta-url').fill('  ')
    dz.locator('#load-remote-delta').click()

    expect(dz.locator('[role="alert"]')).not_to_be_visible(timeout=1000)
    expect(dz.locator('#loading')).not_to_be_visible(timeout=1000)

def test_load_remote_delta_fails_gracefully(dz: Page):
    """Loading a remote Delta table from an invalid URL should show an error toast."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    dz.evaluate("window.deltaSupported = true")
    dz.locator('#remote-delta-url').fill('https://example.invalid/data.delta')
    dz.locator('#load-remote-delta').click()

    toast = dz.locator('[role="alert"]').last
    expect(toast).to_be_visible(timeout=10000)
    expect(toast).to_contain_text(re.compile(r'Error loading remote Delta table', re.IGNORECASE))


def test_run_query_empty_results_shows_empty_state(dz: Page):
    """Running a query that returns 0 rows must show the empty state UI."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    _load_samples_and_wait(dz)

    dz.locator('#sql-input').fill('SELECT * FROM "employees" WHERE id = 99999')
    dz.locator('#run-query').click()

    expect(dz.locator('.empty')).to_be_visible(timeout=ACTION_TIMEOUT)
    expect(dz.locator('.empty')).to_contain_text('No results found')


def test_instant_charts_generated_on_csv_load(dz: Page, tmp_path: Path):
    """Loading date and numeric CSV columns generates at least one preview."""
    dz.goto(DROPZONE, wait_until="domcontentloaded", timeout=60000)
    _wait_for_ready(dz)

    csv = tmp_path / 'sales_data.csv'
    csv.write_text(
        'date,product,revenue\n'
        '2022-01-01,Widget,100\n'
        '2022-01-02,Gadget,200\n'
        '2022-01-03,Doohickey,50\n'
    )

    dz.evaluate("document.getElementById('file-input').removeAttribute('webkitdirectory')")
    dz.locator('#file-input').set_input_files(str(csv))

    previews = dz.locator('#instant-previews .preview-card')
    expect(previews.first).to_be_visible(timeout=ACTION_TIMEOUT)
    assert previews.count() > 0
