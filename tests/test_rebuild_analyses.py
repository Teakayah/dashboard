import pytest
from unittest.mock import patch, MagicMock
from deployment.rebuild_analyses import (
    extract_nhpi,
    extract_statcan_data,
    _clean,
    _inject_const,
    _read_csv,
    rebuild_employment
)
from pathlib import Path


def create_row(
    geo="Ontario",
    ref_date="2023-01",
    value="60.5",
    char="Employment rate",
    gender="Total - Gender",
    age="15 years and over",
    stat="Estimate",
    dtype="Seasonally adjusted",
):
    return {
        "GEO": geo,
        "REF_DATE": ref_date,
        "VALUE": value,
        "Labour force characteristics": char,
        "Gender": gender,
        "Age group": age,
        "Statistics": stat,
        "Data type": dtype,
    }


def create_fed_debt_row(
    geo="Canada",
    gov_sector="Federal government",
    statement="Liabilities",
    ref_date="2023-01",
    value="1500000.0"
):
    return {
        "GEO": geo,
        "Government sectors": gov_sector,
        "Statement of government operations and balance sheet": statement,
        "REF_DATE": ref_date,
        "VALUE": value,
    }


def create_debt_row(
    geo="Ontario",
    ref_date="2023",
    value="10000",
    component="Provincial and territorial governments",
    display="Stocks",
    statement="Liabilities [63]",
):
    return {
        "GEO": geo,
        "REF_DATE": ref_date,
        "VALUE": value,
        "Public sector components": component,
        "Display value": display,
        "Statement of operations and balance sheet": statement,
    }


def create_pop_row(
    geo="Ontario",
    ref_date="2023",
    value="15000000",
    gender="Total - gender",
    age="All ages",
):
    return {
        "GEO": geo,
        "REF_DATE": ref_date,
        "VALUE": value,
        "Gender": gender,
        "Age group": age,
    }


def create_nhpi_row(
    geo="Toronto, Ontario",
    ref_date="2023-01",
    value="120.5",
    measure="Total (house and land)",
    idx_col_name="New housing price indexes",
):
    return {
        "GEO": geo,
        "REF_DATE": ref_date,
        "VALUE": value,
        idx_col_name: measure,
    }


def test_extract_fed_debt_basic():
    rows = [
        # Valid row for 2023
        create_fed_debt_row(ref_date="2023-01", value="1000000.0"),
        # Valid row for 2023, should be averaged with previous
        create_fed_debt_row(ref_date="2023-02", value="2000000.0"),
        # Valid row for 2024
        create_fed_debt_row(ref_date="2024-01", value="3000000.0"),
        # Invalid rows that should be filtered out
        create_fed_debt_row(geo="Ontario"),
        create_fed_debt_row(gov_sector="Provincial and territorial governments"),
        create_fed_debt_row(statement="Assets"),
        create_fed_debt_row(value=".."),
    ]

    result = extract_statcan_data(rows, '10100015')

    # Values should be averaged and divided by 1000
    expected = [
        {"year": 2023, "value": 1500.0},
        {"year": 2024, "value": 3000.0},
    ]

    assert result == expected


def test_extract_fed_debt_empty():
    assert extract_statcan_data([], '10100015') == []


def test_extract_fed_debt_missing_value():
    rows = [
        create_fed_debt_row(ref_date="2023-01", value="1000000.0"),
        create_fed_debt_row(ref_date="2023-02", value="x"),
        create_fed_debt_row(ref_date="2023-03", value=".."),
    ]
    result = extract_statcan_data(rows, '10100015')
    expected = [{"year": 2023, "value": 1000.0}]
    assert result == expected


def test_extract_fed_debt_unordered_years():
    rows = [
        create_fed_debt_row(ref_date="2025-01", value="4000000.0"),
        create_fed_debt_row(ref_date="2023-01", value="1000000.0"),
        create_fed_debt_row(ref_date="2024-01", value="3000000.0"),
    ]
    result = extract_statcan_data(rows, '10100015')
    expected = [
        {"year": 2023, "value": 1000.0},
        {"year": 2024, "value": 3000.0},
        {"year": 2025, "value": 4000.0},
    ]
    assert result == expected


def test_extract_emp_jobs_basic():
    rows = [
        # Valid row for Ontario 2023
        create_row(geo="Ontario", ref_date="2023-01", value="6000.0", char="Employment"),
        create_row(
            geo="Ontario", ref_date="2023-02", value="6100.0", char="Employment"
        ),  # Average for 2023 should be 6050.0
        # Valid row for Quebec 2023
        create_row(geo="Quebec", ref_date="2023-01", value="3000.0", char="Employment"),
        # Valid row for Ontario 2024
        create_row(geo="Ontario", ref_date="2024-01", value="6200.0", char="Employment"),
        # Invalid rows that should be filtered out:
        create_row(char="Employment rate"),  # Wrong characteristic
        create_row(char="Employment", gender="Males"),
        create_row(char="Employment", age="15 to 24 years"),
        create_row(char="Employment", stat="Standard error"),
        create_row(char="Employment", dtype="Unadjusted"),
        create_row(char="Employment", value=".."),
    ]

    result = extract_statcan_data(rows, '14100287', 'empJobs')

    expected = {
        "Ontario": [
            {"year": 2023, "level": 6050.0, "change": None},
            {"year": 2024, "level": 6200.0, "change": 150.0},
        ],
        "Quebec": [{"year": 2023, "level": 3000.0, "change": None}],
    }

    assert result == expected


def test_extract_emp_jobs_empty():
    assert extract_statcan_data([], '14100287', 'empJobs') == {}


def test_extract_emp_jobs_unordered_years():
    rows = [
        create_row(geo="Ontario", ref_date="2025-01", value="6500.0", char="Employment"),
        create_row(geo="Ontario", ref_date="2023-01", value="6000.0", char="Employment"),
        create_row(geo="Ontario", ref_date="2024-01", value="6200.0", char="Employment"),
        create_row(geo="Quebec", ref_date="2024-01", value="3100.0", char="Employment"),
        create_row(geo="Quebec", ref_date="2023-01", value="3000.0", char="Employment"),
    ]
    result = extract_statcan_data(rows, '14100287', 'empJobs')
    expected = {
        "Ontario": [
            {"year": 2023, "level": 6000.0, "change": None},
            {"year": 2024, "level": 6200.0, "change": 200.0},
            {"year": 2025, "level": 6500.0, "change": 300.0},
        ],
        "Quebec": [
            {"year": 2023, "level": 3000.0, "change": None},
            {"year": 2024, "level": 3100.0, "change": 100.0},
        ],
    }
    assert result == expected


def test_extract_emp_jobs_missing_value():
    rows = [
        create_row(geo="Ontario", ref_date="2023-01", value="6000.0", char="Employment"),
        create_row(geo="Ontario", ref_date="2023-02", value="..", char="Employment"),  # Invalid/missing value
        create_row(geo="Ontario", ref_date="2024-01", value="x", char="Employment"),
        create_row(geo="Ontario", ref_date="2025-01", value="6500.0", char="Employment"),
    ]
    result = extract_statcan_data(rows, '14100287', 'empJobs')
    expected = {
        "Ontario": [
            {"year": 2023, "level": 6000.0, "change": None},
            {"year": 2025, "level": 6500.0, "change": 500.0},
        ]
    }
    assert result == expected


def test_extract_emp_rate_basic():
    rows = [
        # Valid row for Ontario 2023
        create_row(geo="Ontario", ref_date="2023-01", value="60.0"),
        create_row(
            geo="Ontario", ref_date="2023-02", value="61.0"
        ),  # Average for 2023 should be 60.5
        # Valid row for Quebec 2023
        create_row(geo="Quebec", ref_date="2023-01", value="62.5"),
        # Valid row for Ontario 2024
        create_row(geo="Ontario", ref_date="2024-01", value="63.3"),
        # Invalid rows that should be filtered out:
        # Wrong characteristic
        create_row(char="Unemployment rate"),
        # Wrong gender
        create_row(gender="Males"),
        # Wrong age group
        create_row(age="15 to 24 years"),
        # Wrong statistic
        create_row(stat="Standard error"),
        # Wrong data type
        create_row(dtype="Unadjusted"),
        # Missing/invalid value
        create_row(value=".."),
        create_row(value="F"),
        create_row(value=""),
    ]

    result = extract_statcan_data(rows, '14100287', 'empRate')

    expected = {
        "Ontario": [{"year": 2023, "value": 60.5}, {"year": 2024, "value": 63.3}],
        "Quebec": [{"year": 2023, "value": 62.5}],
    }

    assert result == expected


def test_extract_emp_rate_empty():
    assert extract_statcan_data([], '14100287', 'empRate') == {}


def test_extract_emp_rate_unordered_years():
    rows = [
        create_row(geo="Ontario", ref_date="2025-01", value="65.0"),
        create_row(geo="Ontario", ref_date="2023-01", value="60.0"),
        create_row(geo="Ontario", ref_date="2024-01", value="63.3"),
    ]
    result = extract_statcan_data(rows, '14100287', 'empRate')
    expected = {
        "Ontario": [
            {"year": 2023, "value": 60.0},
            {"year": 2024, "value": 63.3},
            {"year": 2025, "value": 65.0},
        ]
    }
    assert result == expected


def test_extract_emp_rate_missing_value():
    rows = [
        create_row(geo="Ontario", ref_date="2023-01", value="60.0"),
        create_row(geo="Ontario", ref_date="2023-02", value="x"),
        create_row(geo="Ontario", ref_date="2023-03", value=".."),
    ]
    result = extract_statcan_data(rows, '14100287', 'empRate')
    expected = {"Ontario": [{"year": 2023, "value": 60.0}]}
    assert result == expected


@pytest.mark.parametrize(
    "val, expected",
    [
        ("123", 123.0),
        ("-45.6", -45.6),
        ("0", 0.0),
        ("0.0", 0.0),
        ("1e3", 1000.0),
        ("inf", float("inf")),
        ("-inf", float("-inf")),
    ],
)
def test_clean_valid_floats(val, expected):
    assert _clean(val) == expected


def test_inject_insight():
    from deployment.rebuild_analyses import _inject_insight
    html = "<html><body><!-- insight-inject --><!-- /insight-inject --></body></html>"
    insight = "Test Insight"
    res, changed = _inject_insight(html, insight)
    assert changed
    assert '<div class="insight-badge">Test Insight</div>' in res
    assert "<!-- insight-inject -->" in res
    assert "<!-- /insight-inject -->" in res


def test_inject_insight_no_markers():
    from deployment.rebuild_analyses import _inject_insight
    html = "<html><body>No markers here</body></html>"
    res, changed = _inject_insight(html, "Test")
    assert not changed
    assert res == html


def test_extract_pop_data_basic():
    rows = [
        create_pop_row(geo="Ontario", ref_date="2023", value="15000000"),
        create_pop_row(geo="Ontario", ref_date="2024", value="15300000"),
        create_pop_row(geo="Ontario", ref_date="2025", value="15500000"),
        create_pop_row(geo="Quebec", ref_date="2023", value="8500000"),
        create_pop_row(gender="Males"),
        create_pop_row(age="15 to 24 years"),
        create_pop_row(value=".."),
        create_pop_row(value="x"),
        create_pop_row(value=""),
    ]

    result = extract_statcan_data(rows, '17100005')

    expected = {
        "Ontario": [
            {"year": 2023, "pop": 15000000, "change": None, "pct": None},
            {"year": 2024, "pop": 15300000, "change": 300000, "pct": 2.0},
            {"year": 2025, "pop": 15500000, "change": 200000, "pct": 1.31},
        ],
        "Quebec": [{"year": 2023, "pop": 8500000, "change": None, "pct": None}],
    }

    assert result == expected


def test_extract_pop_data_empty():
    assert extract_statcan_data([], '17100005') == {}


def test_extract_nhpi_basic():
    rows = [
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="120.5", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-02", value="121.0", measure="Total (house and land)"),
        create_nhpi_row(geo="Vancouver, British Columbia", ref_date="2023-01", value="130.0", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="110.0", measure="House only"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="140.0", measure="Land only"),
        # Invalid rows
        create_nhpi_row(measure="Wrong measure"),
        create_nhpi_row(value=".."),
    ]

    result = extract_nhpi(rows)

    expected = {
        "Toronto, Ontario": {
            "Total (house and land)": [
                {"date": "2023-01", "value": 120.5},
                {"date": "2023-02", "value": 121.0},
            ],
            "House only": [
                {"date": "2023-01", "value": 110.0},
            ],
            "Land only": [
                {"date": "2023-01", "value": 140.0},
            ],
        },
        "Vancouver, British Columbia": {
            "Total (house and land)": [
                {"date": "2023-01", "value": 130.0},
            ],
            "House only": [],
            "Land only": [],
        },
    }

    assert result == expected


def test_extract_nhpi_empty():
    assert extract_nhpi([]) == {}


def test_extract_nhpi_missing_idx_col():
    # Pass rows that do not have any column containing 'housing price'
    rows = [
        {"GEO": "Toronto", "REF_DATE": "2023-01", "VALUE": "120.0", "Wrong Column": "Total (house and land)"}
    ]
    result = extract_nhpi(rows)
    assert result == {}



def test_extract_nhpi_missing_value():
    rows = [
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="120.5", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-02", value="..", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-03", value="121.5", measure="Total (house and land)"),
    ]

    result = extract_nhpi(rows)

    expected = [
        {"date": "2023-01", "value": 120.5},
        {"date": "2023-03", "value": 121.5},
    ]

    assert result["Toronto, Ontario"]["Total (house and land)"] == expected


def test_extract_nhpi_unordered_dates():
    rows = [
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-03", value="121.5", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="120.5", measure="Total (house and land)"),
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-02", value="121.0", measure="Total (house and land)"),
    ]

    result = extract_nhpi(rows)

    expected = [
        {"date": "2023-01", "value": 120.5},
        {"date": "2023-02", "value": 121.0},
        {"date": "2023-03", "value": 121.5},
    ]

    assert result["Toronto, Ontario"]["Total (house and land)"] == expected


def test_extract_nhpi_wrong_measure():
    rows = [
        create_nhpi_row(geo="Toronto, Ontario", ref_date="2023-01", value="120.5", measure="Apartment only"),
    ]
    result = extract_nhpi(rows)
    assert result == {}



def test_extract_prov_debt_basic():
    rows = [
        # Valid row for Ontario 2023 (10000 -> 10.0)
        create_debt_row(geo="Ontario", ref_date="2023", value="10000"),
        # Valid row for Quebec 2023 (15000 -> 15.0)
        create_debt_row(geo="Quebec", ref_date="2023", value="15000"),
        # Valid row for Ontario 2024 (25500 -> 25.5)
        create_debt_row(geo="Ontario", ref_date="2024", value="25500"),
        # Invalid rows that should be filtered out:
        # Wrong component
        create_debt_row(component="Federal government"),
        # Wrong display value
        create_debt_row(display="Transactions"),
        # Wrong statement
        create_debt_row(statement="Assets"),
        # Missing/invalid value
        create_debt_row(value=".."),
        create_debt_row(value="x"),
        create_debt_row(value=""),
    ]

    result = extract_statcan_data(rows, '10100017')

    expected = {
        "Ontario": [{"year": 2023, "value": 10.0}, {"year": 2024, "value": 25.5}],
        "Quebec": [{"year": 2023, "value": 15.0}],
    }

    assert result == expected


def test_extract_prov_debt_empty():
    assert extract_statcan_data([], '10100017') == {}


def test_extract_prov_debt_unordered_years():
    rows = [
        create_debt_row(geo="Ontario", ref_date="2025", value="30000"),
        create_debt_row(geo="Ontario", ref_date="2023", value="10000"),
        create_debt_row(geo="Ontario", ref_date="2024", value="20000"),
    ]
    result = extract_statcan_data(rows, '10100017')
    expected = {
        "Ontario": [
            {"year": 2023, "value": 10.0},
            {"year": 2024, "value": 20.0},
            {"year": 2025, "value": 30.0},
        ]
    }
    assert result == expected


def test_clean_nan():
    import math

    val = _clean("nan")
    assert isinstance(val, float) and math.isnan(val)


@pytest.mark.parametrize(
    "val",
    [
        "",
        "..",
        "F",
        "x",
        "E",
        "r",
        "p",
    ],
)
def test_clean_special_strings(val):
    assert _clean(val) is None


@pytest.mark.parametrize(
    "val",
    [
        "not a number",
        "12.34.56",
    ],
)
def test_clean_invalid_strings(val):
    assert _clean(val) is None


def test_inject_const_xss_prevention():
    html = "const DATA = {};\nconsole.log(DATA);"

    # Payload containing characters dangerous in an HTML context
    malicious_data = {
        "text": "<script>alert(1)</script>",
        "desc": "A & B > C",
    }

    new_html, changed = _inject_const(html, "DATA", malicious_data)

    assert changed is True
    # The original unsafe characters should not be in the replaced string
    assert "<script>" not in new_html
    assert "A & B > C" not in new_html

    # They should be replaced by unicode escapes
    assert r"\u003cscript\u003ealert(1)\u003c/script\u003e" in new_html
    assert r"A \u0026 B \u003e C" in new_html


def test_inject_const_regular_data():
    html = "const RAW = {foo: 'bar'};"
    data = {"numbers": [1, 2, 3], "string": "hello\nworld"}

    new_html, changed = _inject_const(html, "RAW", data)
    assert changed is True
    assert 'const RAW={"numbers":[1,2,3],"string":"hello\\nworld"};' in new_html


def test_read_csv_empty_file(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.touch()

    result = _read_csv(empty_file)
    assert result == []


def test_read_csv_valid_file(tmp_path):
    valid_file = tmp_path / "valid.csv"
    # Testing that it strips whitespace from headers (but preserves values as they are now stripped on demand),
    # and properly associates headers with column values.
    valid_file.write_text(" col1 , col2 \n val1 , val2 \n val3 , val4 ")

    result = _read_csv(valid_file)
    assert result == [
        {"col1": " val1 ", "col2": " val2 "},
        {"col1": " val3 ", "col2": " val4 "},
    ]


def test_extract_pop_data_unordered_years():
    rows = [
        create_pop_row(geo="Ontario", ref_date="2025", value="16000000"),
        create_pop_row(geo="Ontario", ref_date="2023", value="15000000"),
        create_pop_row(geo="Ontario", ref_date="2024", value="15500000"),
    ]
    result = extract_statcan_data(rows, '17100005')
    expected = {
        "Ontario": [
            {"year": 2023, "pop": 15000000, "change": None, "pct": None},
            {"year": 2024, "pop": 15500000, "change": 500000, "pct": 3.33},
            {"year": 2025, "pop": 16000000, "change": 500000, "pct": 3.23},
        ]
    }
    assert result == expected


def test_extract_pop_data_missing_value():
    rows = [
        create_pop_row(geo="Ontario", ref_date="2023", value="15000000"),
        create_pop_row(geo="Ontario", ref_date="2024", value="x"),
        create_pop_row(geo="Ontario", ref_date="2025", value="16000000"),
    ]
    result = extract_statcan_data(rows, '17100005')
    expected = {
        "Ontario": [
            {"year": 2023, "pop": 15000000, "change": None, "pct": None},
            {"year": 2025, "pop": 16000000, "change": 1000000, "pct": 6.67},
        ]
    }
    assert result == expected


@patch("pathlib.Path.exists")
@patch("deployment.rebuild_analyses._read_csv")
@patch("deployment.rebuild_analyses.extract_statcan_data")
@patch("pathlib.Path.read_text")
@patch("deployment.rebuild_analyses._inject_const")
@patch("pathlib.Path.write_text")
def test_rebuild_employment_success(
    mock_write_text,
    mock_inject_const,
    mock_read_text,
    mock_extract_statcan_data,
    mock_read_csv,
    mock_exists,
):
    mock_exists.return_value = True
    mock_read_csv.return_value = [{"col": "val"}]
    mock_extract_statcan_data.return_value = {"mock": "data"}
    mock_read_text.return_value = "<html><body></body></html>"
    mock_inject_const.return_value = ("<html><body>new data</body></html>", True)

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is True
    mock_write_text.assert_called_once_with("<html><body>new data</body></html>", encoding="utf-8")


@patch("pathlib.Path.exists")
@patch("deployment.rebuild_analyses._read_csv")
@patch("deployment.rebuild_analyses.extract_statcan_data")
@patch("pathlib.Path.read_text")
@patch("deployment.rebuild_analyses._inject_const")
@patch("deployment.rebuild_analyses._inject_insight")
@patch("pathlib.Path.write_text")
def test_rebuild_employment_insight_grew(
    mock_write_text,
    mock_inject_insight,
    mock_inject_const,
    mock_read_text,
    mock_extract_statcan_data,
    mock_read_csv,
    mock_exists,
):
    mock_exists.return_value = True
    mock_read_csv.return_value = [{"col": "val"}]

    def mock_extract(rows, table_id, variant=None):
        if variant == "empJobs":
            return {"Canada": [{"year": 2024, "change": 150}]}
        return {"mock": "data"}
    mock_extract_statcan_data.side_effect = mock_extract

    mock_read_text.return_value = "<html><body></body></html>"
    # No change to const, but insight changed
    mock_inject_const.return_value = ("<html><body></body></html>", False)
    mock_inject_insight.return_value = ("<html><body>insight</body></html>", True)

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is True
    mock_inject_insight.assert_called_once_with(
        "<html><body></body></html>",
        "<strong>Insight:</strong> In 2024, employment in Canada grew by 150k persons."
    )
    mock_write_text.assert_called_once_with("<html><body>insight</body></html>", encoding="utf-8")


@patch("pathlib.Path.exists")
@patch("deployment.rebuild_analyses._read_csv")
@patch("deployment.rebuild_analyses.extract_statcan_data")
@patch("pathlib.Path.read_text")
@patch("deployment.rebuild_analyses._inject_const")
@patch("deployment.rebuild_analyses._inject_insight")
@patch("pathlib.Path.write_text")
def test_rebuild_employment_insight_decreased(
    mock_write_text,
    mock_inject_insight,
    mock_inject_const,
    mock_read_text,
    mock_extract_statcan_data,
    mock_read_csv,
    mock_exists,
):
    mock_exists.return_value = True
    mock_read_csv.return_value = [{"col": "val"}]

    def mock_extract(rows, table_id, variant=None):
        if variant == "empJobs":
            return {"Canada": [{"year": 2024, "change": -50}]}
        return {"mock": "data"}
    mock_extract_statcan_data.side_effect = mock_extract

    mock_read_text.return_value = "<html><body></body></html>"
    mock_inject_const.return_value = ("<html><body></body></html>", False)
    mock_inject_insight.return_value = ("<html><body>insight</body></html>", True)

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is True
    mock_inject_insight.assert_called_once_with(
        "<html><body></body></html>",
        "<strong>Insight:</strong> In 2024, employment in Canada decreased by 50k persons."
    )


@patch("pathlib.Path.exists")
@patch("deployment.rebuild_analyses._read_csv")
@patch("deployment.rebuild_analyses.extract_statcan_data")
@patch("pathlib.Path.read_text")
@patch("deployment.rebuild_analyses._inject_const")
@patch("pathlib.Path.write_text")
def test_rebuild_employment_insight_exception(
    mock_write_text,
    mock_inject_const,
    mock_read_text,
    mock_extract_statcan_data,
    mock_read_csv,
    mock_exists,
    capsys
):
    mock_exists.return_value = True
    mock_read_csv.return_value = [{"col": "val"}]
    # Trigger an exception by making 'change' missing

    def mock_extract(rows, table_id, variant=None):
        if variant == "empJobs":
            return {"Canada": [{"year": 2024}]} # missing 'change'
        return {"mock": "data"}
    mock_extract_statcan_data.side_effect = mock_extract

    mock_read_text.return_value = "<html><body></body></html>"
    # No const change, exception in insight -> False overall
    mock_inject_const.return_value = ("<html><body></body></html>", False)

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is False
    captured = capsys.readouterr()
    assert "Warning: Failed to generate insight:" in captured.out


@patch("pathlib.Path.exists")
def test_rebuild_employment_missing_csv(mock_exists):
    # Simulate missing files
    mock_exists.return_value = False

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is False


@patch("pathlib.Path.exists")
@patch("deployment.rebuild_analyses._read_csv")
@patch("deployment.rebuild_analyses.extract_statcan_data")
@patch("pathlib.Path.read_text")
@patch("deployment.rebuild_analyses._inject_const")
@patch("pathlib.Path.write_text")
def test_rebuild_employment_no_change(
    mock_write_text,
    mock_inject_const,
    mock_read_text,
    mock_extract_statcan_data,
    mock_read_csv,
    mock_exists,
):
    mock_exists.return_value = True
    mock_read_csv.return_value = [{"col": "val"}]
    mock_extract_statcan_data.return_value = {"mock": "data"}
    mock_read_text.return_value = "<html><body></body></html>"
    # Return unchanged indicator
    mock_inject_const.return_value = ("<html><body></body></html>", False)

    html_path = Path("employment_rate_canada.html")
    result = rebuild_employment(html_path)

    assert result is False
    mock_write_text.assert_not_called()


@patch('deployment.rebuild_analyses.SRC')
@patch('deployment.rebuild_analyses.extract_statcan_data')
@patch('deployment.rebuild_analyses._read_csv')
@patch('deployment.rebuild_analyses._inject_const')
def test_rebuild_nhpi_success(mock_inject, mock_read, mock_extract, mock_src, tmp_path):
    mock_html = tmp_path / "nhpi_test.html"
    mock_html.write_text("dummy html")

    mock_csv = MagicMock()
    mock_csv.exists.return_value = True
    # Setup mock_src to return mock_csv for the specific path chain
    mock_src.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_csv

    mock_read.return_value = [{"some": "data"}]
    mock_extract.return_value = {"extracted": "data"}
    mock_inject.return_value = ("new html with raw", True)

    from deployment.rebuild_analyses import rebuild_nhpi
    result = rebuild_nhpi(mock_html)

    assert result is True
    assert mock_html.read_text() == "new html with raw"
    mock_inject.assert_called_once_with("dummy html", "RAW", {"extracted": "data"})

@patch('deployment.rebuild_analyses.SRC')
def test_rebuild_nhpi_skip_missing_csv(mock_src, tmp_path):
    mock_html = tmp_path / "nhpi_test.html"

    mock_csv = MagicMock()
    mock_csv.exists.return_value = False
    mock_src.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_csv

    from deployment.rebuild_analyses import rebuild_nhpi
    result = rebuild_nhpi(mock_html)

    assert result is False


@patch('deployment.rebuild_analyses.ROOT')
@patch('deployment.rebuild_analyses._inject_const')
def test_rebuild_flood_success(mock_inject, mock_root, tmp_path):
    mock_html = tmp_path / "flood_test.html"
    mock_html.write_text("dummy html")

    mock_json = MagicMock()
    mock_json.exists.return_value = True
    mock_json.read_text.return_value = '{"flood": "data"}'
    mock_root.__truediv__.return_value.__truediv__.return_value = mock_json

    mock_inject.return_value = ("new html with flood data", True)

    from deployment.rebuild_analyses import rebuild_flood
    result = rebuild_flood(mock_html)

    assert result is True
    assert mock_html.read_text() == "new html with flood data"
    mock_inject.assert_called_once_with("dummy html", "DATA", {"flood": "data"})

@patch('deployment.rebuild_analyses.ROOT')
def test_rebuild_flood_skip_missing_json(mock_root, tmp_path):
    mock_html = tmp_path / "flood_test.html"

    mock_json = MagicMock()
    mock_json.exists.return_value = False
    mock_root.__truediv__.return_value.__truediv__.return_value = mock_json

    from deployment.rebuild_analyses import rebuild_flood
    result = rebuild_flood(mock_html)

    assert result is False


@patch('deployment.rebuild_analyses.SRC')
@patch('deployment.rebuild_analyses.extract_statcan_data')
@patch('deployment.rebuild_analyses._read_csv')
@patch('deployment.rebuild_analyses._inject_const')
def test_rebuild_nhpi_no_change(mock_inject, mock_read, mock_extract, mock_src, tmp_path):
    mock_html = tmp_path / "nhpi_test.html"
    mock_html.write_text("dummy html")

    mock_csv = MagicMock()
    mock_csv.exists.return_value = True
    mock_src.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_csv

    mock_read.return_value = [{"some": "data"}]
    mock_extract.return_value = {"extracted": "data"}
    mock_inject.return_value = ("dummy html", False)

    from deployment.rebuild_analyses import rebuild_nhpi
    result = rebuild_nhpi(mock_html)

    assert result is False
    assert mock_html.read_text() == "dummy html"

@patch('deployment.rebuild_analyses.ROOT')
@patch('deployment.rebuild_analyses._inject_const')
def test_rebuild_flood_no_change(mock_inject, mock_root, tmp_path):
    mock_html = tmp_path / "flood_test.html"
    mock_html.write_text("dummy html")

    mock_json = MagicMock()
    mock_json.exists.return_value = True
    mock_json.read_text.return_value = '{"flood": "data"}'
    mock_root.__truediv__.return_value.__truediv__.return_value = mock_json

    mock_inject.return_value = ("dummy html", False)

    from deployment.rebuild_analyses import rebuild_flood
    result = rebuild_flood(mock_html)

    assert result is False
    assert mock_html.read_text() == "dummy html"
def test_extract_invalid_year():
    rows = [
        create_row(geo="Ontario", ref_date="ABCD-01", value="100.0")
    ]
    result = extract_statcan_data(rows, '14100287', 'empRate')
    assert result == {}

def test_extract_no_config():
    result = extract_statcan_data([], '99999999', 'empRate')
    assert result == []

def test_extract_generic_table():
    rows = [
        {"GEO": "Canada", "REF_DATE": "2023-01", "VALUE": "100.0", "Government sectors": "Federal government", "Statement of government operations and balance sheet": "Liabilities"}
    ]
    result = extract_statcan_data(rows, '10100015')
    assert result == [{"year": 2023, "value": 0.1}]

def test_extract_memoization():
    rows = [
        create_row(geo="Ontario", gender="  Total - Gender  ", ref_date="2023-01", value="100.0")
    ]
    result = extract_statcan_data(rows, '14100287', 'empRate')
    assert result == {"Ontario": [{"year": 2023, "value": 100.0}]}

@patch.dict("deployment.rebuild_analyses.EXTRACTION_CONFIGS", {"99999999": {"default_filters": {"GEO": "Canada"}}})
def test_extract_fallback_return():
    rows = [
        {"GEO": "Canada", "REF_DATE": "2023-01", "VALUE": "100.0"}
    ]
    result = extract_statcan_data(rows, '99999999')
    assert result == {"Canada": {2023: [100.0]}}

@patch('deployment.rebuild_analyses.ROOT')
def test_main_success_with_changes(mock_root):
    mock_html = MagicMock()
    mock_html.exists.return_value = True
    mock_root.__truediv__.return_value = mock_html

    mock_rebuild_fn = MagicMock(return_value=True)
    with patch('deployment.rebuild_analyses.REBUILDERS', {"test.html": mock_rebuild_fn}):
        from deployment.rebuild_analyses import main
        result = main()
        assert result == 1
        mock_rebuild_fn.assert_called_once_with(mock_html)


@patch('deployment.rebuild_analyses.ROOT')
def test_main_skip_missing_file(mock_root):
    mock_html = MagicMock()
    mock_html.exists.return_value = False
    mock_root.__truediv__.return_value = mock_html

    mock_rebuild_fn = MagicMock()
    with patch('deployment.rebuild_analyses.REBUILDERS', {"test.html": mock_rebuild_fn}):
        from deployment.rebuild_analyses import main
        result = main()
        assert result == 0
        mock_rebuild_fn.assert_not_called()


@patch('deployment.rebuild_analyses.ROOT')
def test_main_exception_handling(mock_root, capsys):
    mock_html = MagicMock()
    mock_html.exists.return_value = True
    mock_root.__truediv__.return_value = mock_html

    mock_rebuild_fn = MagicMock(side_effect=Exception("Test Exception"))
    with patch('deployment.rebuild_analyses.REBUILDERS', {"test.html": mock_rebuild_fn}):
        from deployment.rebuild_analyses import main
        result = main()
        assert result == 0
        mock_rebuild_fn.assert_called_once_with(mock_html)
    captured = capsys.readouterr()
    assert "ERROR rebuilding test.html: Test Exception" in captured.out

def test_extract_statcan_data_invalid_ref_date():
    from deployment.rebuild_analyses import extract_statcan_data
    # Need to match ALL default filters for 17100005 to process REF_DATE
    from deployment.config import EXTRACTION_CONFIGS
    row = {"REF_DATE": "bad_", "GEO": "Ontario", "VALUE": "16000000"}
    row.update(EXTRACTION_CONFIGS["17100005"]["default_filters"])

    row2 = {"REF_DATE": "2025", "GEO": "Ontario", "VALUE": "16500000"}
    row2.update(EXTRACTION_CONFIGS["17100005"]["default_filters"])

    result = extract_statcan_data([row, row2], '17100005')
    assert "Ontario" in result
    assert len(result["Ontario"]) == 1

def test_extract_statcan_data_missing_config():
    from deployment.rebuild_analyses import extract_statcan_data
    result = extract_statcan_data([{"VALUE": "100"}], "99999999")
    assert result == []

@patch('deployment.rebuild_analyses.extract_nhpi')
def test_extract_statcan_data_nhpi(mock_extract_nhpi):
    from deployment.rebuild_analyses import extract_statcan_data
    mock_extract_nhpi.return_value = {"nhpi": "data"}
    rows = [{"REF_DATE": "2020-01", "GEO": "Canada"}]
    res = extract_statcan_data(rows, "18100205")
    mock_extract_nhpi.assert_called_once_with(rows)
    assert res == {"nhpi": "data"}

def test_extract_statcan_data_strip_optimization():
    from deployment.rebuild_analyses import extract_statcan_data
    from deployment.config import EXTRACTION_CONFIGS

    # 14100287 has default_filters and variants we can target
    row = {
        "REF_DATE": "2023-01",
        "GEO": "Ontario",
        "VALUE": "15000000"
    }
    # Add whitespace to ALL filter values to trigger the `val.strip() == v` branch
    filters = EXTRACTION_CONFIGS["14100287"]["default_filters"].copy()
    filters.update(EXTRACTION_CONFIGS["14100287"]["variants"]["empJobs"])
    for k, v in filters.items():
        row[k] = f" {v} " # Add whitespace to trigger optimization branch

    result = extract_statcan_data([row], '14100287', 'empJobs')
    assert "Ontario" in result

    # Check that at least one value was stripped in place
    for k, v in filters.items():
        assert row[k] == v  # Value should be modified in place

def test_extract_statcan_data_general_buckets():
    from deployment.rebuild_analyses import extract_statcan_data
    from deployment.config import EXTRACTION_CONFIGS

    # Target table_id without variant that falls through to return buckets directly
    EXTRACTION_CONFIGS["88888888"] = {"default_filters": {"test": "val"}}

    row = {
        "REF_DATE": "2023-01",
        "GEO": "Ontario",
        "VALUE": "100",
        "test": "val"
    }

    result = extract_statcan_data([row], '88888888')
    assert "Ontario" in result
    assert result["Ontario"][2023] == [100.0]

    # Cleanup
    del EXTRACTION_CONFIGS["88888888"]

@patch("sys.exit")
def test_script_entrypoint(mock_exit):
    import importlib.util
    from pathlib import Path
    with patch("deployment.rebuild_analyses.main", return_value=0):
        path = Path(__file__).parent.parent / 'deployment' / 'rebuild_analyses.py'
        spec = importlib.util.spec_from_file_location('__main__', path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        mock_exit.assert_called_once_with(0)
