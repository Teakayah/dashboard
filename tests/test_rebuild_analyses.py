import pytest
from deployment.rebuild_analyses import (
    extract_emp_rate,
    extract_fed_debt,
    extract_prov_debt,
    _clean,
    _inject_const
)


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

    result = extract_fed_debt(rows)

    # Values should be averaged and divided by 1000
    expected = [
        {"year": 2023, "value": 1500.0},
        {"year": 2024, "value": 3000.0},
    ]

    assert result == expected


def test_extract_fed_debt_empty():
    assert extract_fed_debt([]) == []


def test_extract_fed_debt_missing_value():
    rows = [
        create_fed_debt_row(ref_date="2023-01", value="1000000.0"),
        create_fed_debt_row(ref_date="2023-02", value="x"),
        create_fed_debt_row(ref_date="2023-03", value=".."),
    ]
    result = extract_fed_debt(rows)
    expected = [{"year": 2023, "value": 1000.0}]
    assert result == expected


def test_extract_fed_debt_unordered_years():
    rows = [
        create_fed_debt_row(ref_date="2025-01", value="4000000.0"),
        create_fed_debt_row(ref_date="2023-01", value="1000000.0"),
        create_fed_debt_row(ref_date="2024-01", value="3000000.0"),
    ]
    result = extract_fed_debt(rows)
    expected = [
        {"year": 2023, "value": 1000.0},
        {"year": 2024, "value": 3000.0},
        {"year": 2025, "value": 4000.0},
    ]
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

    result = extract_emp_rate(rows)

    expected = {
        "Ontario": [{"year": 2023, "value": 60.5}, {"year": 2024, "value": 63.3}],
        "Quebec": [{"year": 2023, "value": 62.5}],
    }

    assert result == expected


def test_extract_emp_rate_empty():
    assert extract_emp_rate([]) == {}


def test_extract_emp_rate_unordered_years():
    rows = [
        create_row(geo="Ontario", ref_date="2025-01", value="65.0"),
        create_row(geo="Ontario", ref_date="2023-01", value="60.0"),
        create_row(geo="Ontario", ref_date="2024-01", value="63.3"),
    ]
    result = extract_emp_rate(rows)
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
    result = extract_emp_rate(rows)
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

    result = extract_prov_debt(rows)

    expected = {
        "Ontario": [{"year": 2023, "value": 10.0}, {"year": 2024, "value": 25.5}],
        "Quebec": [{"year": 2023, "value": 15.0}],
    }

    assert result == expected


def test_extract_prov_debt_empty():
    assert extract_prov_debt([]) == {}


def test_extract_prov_debt_unordered_years():
    rows = [
        create_debt_row(geo="Ontario", ref_date="2025", value="30000"),
        create_debt_row(geo="Ontario", ref_date="2023", value="10000"),
        create_debt_row(geo="Ontario", ref_date="2024", value="20000"),
    ]
    result = extract_prov_debt(rows)
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
