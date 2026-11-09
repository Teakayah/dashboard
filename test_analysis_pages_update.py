import re

with open('tests/test_analysis_pages.py', 'r') as f:
    content = f.read()

# Replace test_employment_all_tabs_are_clickable
content = re.sub(
    r"        tab\.click\(\)\n        page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n        # Target panel is active\n        active = page\.locator\(f'#panel-\{tab_id\}'\)\n        assert 'active' in \(active\.get_attribute\('class'\) or ''\), \(\n            f'Panel #\{tab_id\} not active after clicking \"\{label\}\"'\n        \)",
    r"        tab.click()\n\n        # Target panel is active\n        active = page.locator(f'#panel-{tab_id}')\n        expect(active).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_employment_charts_have_height_in_each_tab
content = re.sub(
    r"        page\.locator\('\.tab'\)\.nth\(i\)\.click\(\)\n        page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n        height = page\.evaluate\(\n            f\"document\.getElementById\('\{canvas_id\}'\)\?\.offsetHeight \?\? 0\"\n        \)\n        assert height > 0, \(\n            f'Canvas #\{canvas_id\} has zero height on tab \"\{tab_id\}\"'\n        \)",
    r"        page.locator('.tab').nth(i).click()\n\n        page.wait_for_function(f\"document.getElementById('{canvas_id}')?.offsetHeight > 0\")",
    content
)

# Replace test_employment_overview_toggle_switches_chart
content = re.sub(
    r"    # Ensure we're on the rate tab\n    page\.locator\('\.tab'\)\.nth\(0\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)",
    r"    # Ensure we're on the rate tab\n    page.locator('.tab').nth(0).click()\n    expect(page.locator('#panel-rate')).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_nhpi_year_button_click_activates_it
content = re.sub(
    r"    target\.click\(\)\n    page\.wait_for_timeout\(400\)\n\n    classes = target\.get_attribute\('class'\) or ''\n    assert 'active' in classes, \(\n        f'Year button did not get \"active\" class after click \(classes: \{classes!r\}\)'\n    \)",
    r"    target.click()\n    expect(target).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_flood_all_tabs_switch_panels
content = re.sub(
    r"        page\.locator\(f\"\.tab\[onclick\*=\\\"\'\{tab_id\}\'\\\"\]\"\)\.click\(\)\n        page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n        active = page\.locator\(f'#panel-\{tab_id\}'\)\n        classes = active\.get_attribute\('class'\) or ''\n        assert 'active' in classes, \(\n            f'#panel-\{tab_id\} not active after clicking tab \"\{tab_id\}\"'\n        \)",
    r"        page.locator(f\".tab[onclick*=\\\"'{tab_id}'\\\"]\").click()\n\n        active = page.locator(f'#panel-{tab_id}')\n        expect(active).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_flood_gauge_chart_has_height
content = re.sub(
    r"    page\.locator\(\"\.tab\[onclick\*=\\\"\'gauge\'\\\"\]\"\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n    height = page\.evaluate\(\n        \"document\.getElementById\('gaugeChart'\)\?\.offsetHeight \?\? 0\"\n    \)\n    assert height > 0, 'gaugeChart canvas has zero height'",
    r"    page.locator(\".tab[onclick*=\\\"'gauge'\\\"]\").click()\n\n    page.wait_for_function(\"document.getElementById('gaugeChart')?.offsetHeight > 0\")",
    content
)

# Replace test_flood_slider_updates_britannia_level
content = re.sub(
    r"    page\.locator\(\"\.tab\[onclick\*=\\\"\'gauge\'\\\"\]\"\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)",
    r"    page.locator(\".tab[onclick*=\\\"'gauge'\\\"]\").click()\n    expect(page.locator('#panel-gauge')).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_flood_slider_updates_hull_level
content = re.sub(
    r"    page\.locator\(\"\.tab\[onclick\*=\\\"\'gauge\'\\\"\]\"\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)",
    r"    page.locator(\".tab[onclick*=\\\"'gauge'\\\"]\").click()\n    expect(page.locator('#panel-gauge')).to_have_class(re.compile(r'\\bactive\\b'))",
    content
)

# Replace test_flood_history_chart_renders
content = re.sub(
    r"    page\.locator\(\"\.tab\[onclick\*=\\\"\'history\'\\\"\]\"\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n    height = page\.evaluate\(\n        \"document\.getElementById\('historyChart'\)\?\.offsetHeight \?\? 0\"\n    \)\n    assert height > 0, 'historyChart canvas has zero height on history tab'",
    r"    page.locator(\".tab[onclick*=\\\"'history'\\\"]\").click()\n\n    page.wait_for_function(\"document.getElementById('historyChart')?.offsetHeight > 0\")",
    content
)

# Replace test_flood_snowpack_chart_renders
content = re.sub(
    r"    page\.locator\(\"\.tab\[onclick\*=\\\"\'snowpack\'\\\"\]\"\)\.click\(\)\n    page\.wait_for_timeout\(TAB_TIMEOUT\)\n\n    height = page\.evaluate\(\"\"\"\n        \(\) => \{\n            const canvas = document\.querySelector\('#panel-snowpack canvas'\);\n            return canvas \? canvas\.offsetHeight : 0;\n        \}\n    \"\"\"\)\n    assert height > 0, 'Snowpack panel canvas has zero height'",
    r"    page.locator(\".tab[onclick*=\\\"'snowpack'\\\"]\").click()\n\n    page.wait_for_function(\"() => { const c = document.querySelector('#panel-snowpack canvas'); return c ? c.offsetHeight > 0 : false; }\")",
    content
)

with open('tests/test_analysis_pages.py', 'w') as f:
    f.write(content)
