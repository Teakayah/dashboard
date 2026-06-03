import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import importlib.util
import sys

def run_script(script_name):
    path = Path(__file__).parent.parent.parent / 'scripts' / script_name
    spec = importlib.util.spec_from_file_location('__main__', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_script_as_module(script_name, module_name):
    path = Path(__file__).parent.parent.parent / 'scripts' / script_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_benchmark_final():
    csv_data = "REF_DATE,GEO,Labour force characteristics,Gender,Age group,Statistics,Data type,VALUE\n2020-01,Canada,Employment rate,Total - Gender,15 years and over,Estimate,Seasonally adjusted,10.5\n"
    with patch('builtins.open', mock_open(read_data=csv_data)):
        module = load_script_as_module('benchmark_final_test.py', 'benchmark_final_test')

        # Test clean
        assert module._clean(' 10.5 ') == 10.5
        assert module._clean('..') is None
        assert module._clean('F') is None
        assert module._clean('invalid') is None

        # Test logic
        rows = [
            {'Gender': 'Total - Gender', 'Age group': '15 years and over', 'Labour force characteristics': 'Employment rate', 'Data type': 'Seasonally adjusted', 'Statistics': 'Estimate', 'VALUE': '10.5', 'REF_DATE': '2020-01', 'GEO': 'Canada'},
            {'Gender': 'Male', 'Age group': '15 years and over', 'Labour force characteristics': 'Employment rate', 'Data type': 'Seasonally adjusted', 'Statistics': 'Estimate', 'VALUE': '10.5', 'REF_DATE': '2020-01', 'GEO': 'Canada'}
        ]

        res1 = module.extract_emp_rate_reordered(rows)
        assert res1['Canada'][2020] == [10.5]

        res2 = module.extract_emp_rate_opt(rows)
        assert res2['Canada'][2020] == [10.5]

        assert module._read_csv_orig("fake") is not None
        assert module._read_csv_stripped(Path("fake")) is not None

        with patch('builtins.open', mock_open(read_data="")):
            assert module._read_csv_stripped(Path("fake")) == []

        with patch('pathlib.Path.exists', return_value=True):
            with patch('time.time', side_effect=[1, 2, 3, 4]):
                with patch('builtins.print') as mock_print:
                    run_script('benchmark_final_test.py')
                    assert mock_print.call_count >= 2

        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit') as mock_exit:
                    run_script('benchmark_final_test.py')
                    assert mock_print.call_count >= 1
                    mock_exit.assert_called_once_with(0)


def test_benchmark_generate_index():
    with patch('time.time', side_effect=[1, 2]):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print') as mock_print:
                run_script('benchmark_generate_index.py')
                assert mock_run.call_count == 1
                assert mock_print.call_count >= 1

def test_dummy_data_gen():
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        with patch('builtins.open', mock_open()) as m_open:
            with patch('csv.DictWriter') as MockWriter:
                instance = MockWriter.return_value
                run_script('dummy_data_gen.py')

                assert mock_mkdir.call_count >= 1
                assert m_open.call_count == 4
                assert instance.writerow.call_count == 400000
                assert instance.writeheader.call_count == 4

def test_generate_icons():
    with patch('PIL.Image.new') as mock_image_new:
        with patch('PIL.ImageDraw.Draw') as mock_draw:
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.print') as mock_print:
                    module = load_script_as_module('generate_icons.py', 'generate_icons')

                    # Test logic
                    mock_img = MagicMock()
                    mock_image_new.return_value = mock_img

                    module.generate_icon(100, "fake.png")

                    assert mock_image_new.call_count == 1
                    assert mock_img.save.call_count == 1
                    mock_img.save.assert_called_with("fake.png")

def test_generate_icons_main():
    with patch('PIL.Image.new') as mock_image_new:
        with patch('PIL.ImageDraw.Draw') as mock_draw:
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.print') as mock_print:
                    run_script('generate_icons.py')
                    assert mock_makedirs.call_count == 1
                    assert mock_print.call_count == 3
