from scripts.benchmark_final_test import extract_emp_rate_reordered


def test_extract_emp_rate_reordered_happy_path():
    rows = [
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': ' 65.5 ',
            'REF_DATE': '2023-01',
            'GEO': ' Ontario '
        },
        {
            'Gender': ' Total - Gender ',
            'Age group': ' 15 years and over ',
            'Labour force characteristics': ' Employment rate ',
            'Data type': ' Seasonally adjusted ',
            'Statistics': ' Estimate ',
            'VALUE': '66.0',
            'REF_DATE': '2023-02',
            'GEO': 'Ontario'
        }
    ]
    result = extract_emp_rate_reordered(rows)
    assert 'Ontario' in result
    assert 2023 in result['Ontario']
    assert result['Ontario'][2023] == [65.5, 66.0]

def test_extract_emp_rate_reordered_unmatched_rows():
    rows = [
        {
            'Gender': 'Men',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '65.5',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 to 24 years',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '65.5',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Unemployment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '65.5',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Unadjusted',
            'Statistics': 'Estimate',
            'VALUE': '65.5',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Standard error',
            'VALUE': '65.5',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        }
    ]
    result = extract_emp_rate_reordered(rows)
    assert len(result) == 0

def test_extract_emp_rate_reordered_invalid_values():
    rows = [
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': ' .. ',
            'REF_DATE': '2023-01',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': 'F',
            'REF_DATE': '2023-02',
            'GEO': 'Ontario'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': 'not a number',
            'REF_DATE': '2023-03',
            'GEO': 'Ontario'
        }
    ]
    result = extract_emp_rate_reordered(rows)
    assert len(result) == 0

def test_extract_emp_rate_reordered_empty():
    result = extract_emp_rate_reordered([])
    assert len(result) == 0
