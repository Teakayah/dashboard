import importlib.util
from pathlib import Path


def load_benchmark_module():
    path = Path(__file__).parent.parent / 'scripts' / 'benchmark_final_test.py'
    spec = importlib.util.spec_from_file_location('benchmark_final_test', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_extract_emp_rate_reordered_happy_path():
    module = load_benchmark_module()
    rows = [
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '62.1',
            'REF_DATE': '2023-02',
            'GEO': 'Canada'
        }
    ]
    result = module.extract_emp_rate_reordered(rows)
    assert 'Canada' in result
    assert 2023 in result['Canada']
    assert result['Canada'][2023] == [61.5, 62.1]

def test_extract_emp_rate_reordered_ignores_unmatched():
    module = load_benchmark_module()
    rows = [
        # Wrong Gender
        {
            'Gender': 'Men',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        # Wrong Age group
        {
            'Gender': 'Total - Gender',
            'Age group': '15 to 24 years',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        # Wrong Labour force characteristics
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Unemployment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        # Wrong Data type
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Unadjusted',
            'Statistics': 'Estimate',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        # Wrong Statistics
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Standard error',
            'VALUE': '61.5',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        }
    ]
    result = module.extract_emp_rate_reordered(rows)
    assert not result

def test_extract_emp_rate_reordered_ignores_invalid_value():
    module = load_benchmark_module()
    rows = [
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': '..',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': 'F',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        },
        {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Labour force characteristics': 'Employment rate',
            'Data type': 'Seasonally adjusted',
            'Statistics': 'Estimate',
            'VALUE': 'not a number',
            'REF_DATE': '2023-01',
            'GEO': 'Canada'
        }
    ]
    result = module.extract_emp_rate_reordered(rows)
    assert not result

def test_extract_emp_rate_reordered_handles_whitespace():
    module = load_benchmark_module()
    rows = [
        {
            'Gender': '  Total - Gender  ',
            'Age group': ' 15 years and over ',
            'Labour force characteristics': '\tEmployment rate\n',
            'Data type': ' Seasonally adjusted ',
            'Statistics': ' Estimate ',
            'VALUE': ' 65.5 ',
            'REF_DATE': '2023-01',
            'GEO': '  Canada  '
        }
    ]
    result = module.extract_emp_rate_reordered(rows)
    assert 'Canada' in result
    assert 2023 in result['Canada']
    assert result['Canada'][2023] == [65.5]
