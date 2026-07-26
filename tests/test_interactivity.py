from playwright.sync_api import Page, expect
from pathlib import Path
from helpers import (
    BASE as BASE_URL,
    DROPZONE_URL,
    ACTION_TIMEOUT,
    wait_for_duckdb_ready,
    load_samples,
)

REPO_ROOT = Path(__file__).parent.parent
FLOOD_URL = f"{BASE_URL}/flood_risk_gatineau_ottawa.html"


LOAD_TIMEOUT = 8_000


def _load_page(page: Page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=LOAD_TIMEOUT)
    except Exception:
        pass


class TestIndexSearch:
    def test_search_filters_cards(self, page: Page):
        _load_page(page, BASE_URL)
        search = page.locator("#search")
        expect(search).to_be_visible()

        total = page.locator(".card").count()
        assert total > 0

        # Type a string that matches nothing
        search.fill("xyzzznotarealanything")
        expect(page.locator(".card:not(.hidden)")).to_have_count(0)

        # Clear -> cards reappear
        search.fill("")
        expect(page.locator(".card:not(.hidden)")).to_have_count(total)


class TestDropzoneButtons:
    def test_load_samples_button_works(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)

        # Before loading, schema should mention nothing
        expect(dz.locator("#schema-display")).not_to_contain_text("employees")

        dz.locator("#load-samples").click()
        dz.wait_for_function(
            "document.getElementById('schema-display').textContent.includes('employees')",
            timeout=ACTION_TIMEOUT,
        )

        expect(dz.locator("#schema-display")).to_contain_text("employees")
        expect(dz.locator("#schema-display")).to_contain_text("departments")

    def test_generate_join_validation(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        # Don't select anything — just click
        dz.locator("#generate-join").click()
        toast = dz.locator('[role="alert"]').last
        toast.wait_for(state="visible", timeout=3000)
        assert "select both tables" in toast.inner_text().lower()

    def test_chart_builder_appears_after_loading_data(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        expect(dz.locator("#chart-builder")).to_be_visible()

    def test_chart_builder_validation(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        dz.locator("#generate-chart").click()
        toast = dz.locator('[role="alert"]').last
        toast.wait_for(state="visible", timeout=3000)
        assert "select both x and y" in toast.inner_text().lower()

    def test_export_db_button_triggers_download_or_error(self, dz: Page):
        """Export Database must either download a file or show an error — no silent crash."""
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        import os
        with dz.expect_download(timeout=8_000) as dl_info:
            dz.locator("#export-db").click()
        dl = dl_info.value
        assert dl.suggested_filename.endswith(".db"), (
            f"Unexpected filename: {dl.suggested_filename!r}"
        )
        assert os.path.getsize(dl.path()) > 0, "Downloaded file is empty"

    def test_clear_data_button_wipes_schema(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        expect(dz.locator("#schema-display")).to_contain_text("employees")

        # Confirm the dialog
        dz.on("dialog", lambda d: d.accept())
        dz.locator("#clear-data").click()

        expect(dz.locator("#schema-display")).to_be_empty()
        expect(dz.locator("#instant-previews")).to_be_empty()

    def test_clear_data_button_dismiss_keeps_schema(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)
        expect(dz.locator("#schema-display")).to_contain_text("employees")

        # Dismiss the dialog
        dz.on("dialog", lambda d: d.dismiss())
        dz.locator("#clear-data").click()

        expect(dz.locator("#schema-display")).to_contain_text("employees")

    def test_run_query_button_executes_sql(self, dz: Page):
        dz.goto(DROPZONE_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_duckdb_ready(dz)
        load_samples(dz)

        # Clear existing query and type a new one
        sql_input = dz.locator("#sql-input")
        sql_input.fill("SELECT COUNT(*) AS total FROM employees")

        # Wait for the button to be enabled after typing
        run_btn = dz.locator("#run-query")
        expect(run_btn).to_be_enabled(timeout=ACTION_TIMEOUT)

        # Click run and verify results appear
        run_btn.click()

        # Verify the Grid.js table appears with our results
        expect(dz.locator("#results")).to_contain_text("total")
        expect(dz.locator("#results")).to_contain_text("5")


class TestFloodPageButtons:
    def test_share_button_exists(self, page: Page):
        _load_page(page, FLOOD_URL)
        expect(page.locator(".share-btn")).to_be_visible()

    def test_reset_button_reverts_offset(self, page: Page):
        _load_page(page, FLOOD_URL)
        slider = page.locator("#levelSlider")
        slider.evaluate("el => { el.value = '1.5'; el.dispatchEvent(new Event('input')); }")
        expect(page.locator("#offsetDisplay")).to_contain_text("1.50m")

        page.locator('button:has-text("Reset")').click()
        expect(page.locator("#offsetDisplay")).to_contain_text("0.00m")
        expect(slider).to_have_value("0")

    def test_slider_updates_regional_levels(self, page: Page):
        _load_page(page, FLOOD_URL)

        # Get initial values
        low_hull = float(page.locator("#hullDisplay").inner_text())

        # Move slider up
        page.locator("#levelSlider").evaluate("el => { el.value = '2.0'; el.dispatchEvent(new Event('input')); }")
        page.wait_for_timeout(300)

        high_hull = float(page.locator("#hullDisplay").inner_text())

        assert high_hull > low_hull, (
            f"Hull level did not increase when slider went up: {low_hull} → {high_hull}"
        )
        assert high_hull > 0, "Hull level is zero at slider high value"

    def test_slider_offset_display_updates(self, page: Page):
        _load_page(page, FLOOD_URL)
        slider = page.locator("#levelSlider")
        display = page.locator("#offsetDisplay")

        slider.evaluate("el => { el.value = '-0.5'; el.dispatchEvent(new Event('input')); }")
        expect(display).to_contain_text("-0.50m")

        slider.evaluate("el => { el.value = '2.25'; el.dispatchEvent(new Event('input')); }")
        expect(display).to_contain_text("2.25m")
