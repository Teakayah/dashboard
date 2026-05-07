import pytest
from unittest.mock import patch, MagicMock
from deployment.rebuild_analyses import (
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

    result = extract_statcan_data(rows, '18100205')

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
    assert extract_statcan_data([], '18100205') == {}


def test_extract_nhpi_missing_idx_col():
    # Pass rows that do not have any column containing 'housing price'
    rows = [
        {"GEO": "Toronto", "REF_DATE": "2023-01", "VALUE": "120.0", "Wrong Column": "Total (house and land)"}
    ]
    result = extract_statcan_data(rows, '18100205')
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

from unittest.mock import patch, MagicMock

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
