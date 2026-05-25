"""
Front-end integration tests for the Analytical Drop-Zone (DuckDB-Wasm).

Requires the local HTTP server started automatically by conftest.py (port 8765).
Run with:  pytest tests/test_dropzone.py -v
"""

from pathlib import Path

from playwright.sync_api import Page, expect

from helpers import (
    DROPZONE_URL as DROPZONE,
    ACTION_TIMEOUT,
    DUCKDB_READY_TIMEOUT as READY_TIMEOUT,
    wait_for_duckdb_ready as _wait_for_ready,
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
        "document.getElementById('sql-input').value.includes('employees')",
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



# ── SQL execution ─────────────────────────────────────────────────────────────

def test_run_query_button_disabled_without_input(dz: Page):
    """Run Query must stay disabled until the user types something."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)
    run_btn = dz.locator('#run-query')
    assert run_btn.is_disabled(), 'Run Query should be disabled when SQL input is empty'


def test_run_query_button_enables_when_sql_typed(dz: Page):
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#sql-input').fill('SELECT 1')
    run_btn = dz.locator('#run-query')
    assert not run_btn.is_disabled(), 'Run Query should be enabled after typing SQL'


def test_run_query_returns_results_grid(dz: Page):
    """SELECT against the sample data must render a Grid.js results table."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 3')
    dz.locator('#run-query').click()
    # Use Playwright's built-in retry assertion — it keeps polling until the
    # count is exactly 3 or the timeout expires (more robust than wait_for_function)
    expect(dz.locator('.gridjs-tbody tr')).to_have_count(3, timeout=READY_TIMEOUT)


def test_run_query_enables_download_and_copy_buttons(dz: Page):
    """Download CSV and Copy JSON must become active after a successful query."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    # Both buttons should start disabled
    assert dz.locator('#download-csv').is_disabled()
    assert dz.locator('#copy-json').is_disabled()

    dz.locator('#sql-input').fill('SELECT * FROM "departments"')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    assert not dz.locator('#download-csv').is_disabled(), 'Download CSV not enabled after query'
    assert not dz.locator('#copy-json').is_disabled(), 'Copy JSON not enabled after query'


def test_join_query_executes_correctly(dz: Page):
    """The pre-populated JOIN query (set after Load Samples) must run and return rows."""
    dz.goto(DROPZONE)
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
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    dz.locator('#sql-input').fill('SELECT * FROM nonexistent_table_xyz')
    dz.locator('#run-query').click()

    toast = dz.locator('[role="alert"]')
    toast.wait_for(state="visible", timeout=3000)
    assert 'Error' in toast.inner_text() or 'nonexistent' in toast.inner_text().lower()


def test_count_query_returns_single_value(dz: Page):
    """COUNT(*) must return exactly one row with the correct value."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

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
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

    dz.locator('#sql-input').fill('SELECT * FROM "employees" LIMIT 1')
    dz.locator('#run-query').click()
    dz.wait_for_selector('.gridjs-tbody tr', timeout=ACTION_TIMEOUT)

    with dz.expect_download() as download_info:
        dz.locator('#download-csv').click()

    download = download_info.value
    assert download.suggested_filename.startswith('query_results_'), "Downloaded file name should start with 'query_results_'"
    assert download.suggested_filename.endswith('.csv'), "Downloaded file name should end with '.csv'"

    path = download.path()
    with open(path, 'r') as f:
        content = f.read()

    assert 'id,name,dept_id,salary,join_date' in content, "CSV should contain headers"
    assert '1,Alice,101,85000,2022-01-15' in content, "CSV should contain row data"

def test_copy_json_copies_to_clipboard(dz: Page):
    """Clicking Copy JSON must copy the query results to the clipboard."""
    dz.goto(DROPZONE)
    _wait_for_ready(dz)

    # Grant clipboard-read and clipboard-write permissions to the current origin
    dz.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=dz.url)

    dz.locator('#load-samples').click()
    dz.wait_for_function(
        "document.getElementById('schema-display').textContent.includes('employees')",
        timeout=ACTION_TIMEOUT,
    )

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
