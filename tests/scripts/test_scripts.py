from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import importlib.util

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

def test_generate_icons(tmp_path):
    from PIL import Image
    with patch('builtins.print'):
        module = load_script_as_module('generate_icons.py', 'generate_icons')

        test_file = tmp_path / "test_100.png"
        module.generate_icon(100, str(test_file))

        assert test_file.exists()
        with Image.open(test_file) as img:
            assert img.size == (100, 100)
            assert img.mode == 'RGBA'
            assert img.getpixel((50, 50)) == (255, 255, 255, 255)

def test_generate_icons_main(tmp_path, monkeypatch):
    from PIL import Image
    monkeypatch.chdir(tmp_path)
    with patch('builtins.print'):
        run_script('generate_icons.py')

    assert (tmp_path / "assets" / "icons").exists()

    icon_192 = tmp_path / "assets" / "icons" / "icon-192.png"
    icon_512 = tmp_path / "assets" / "icons" / "icon-512.png"
    icon_maskable = tmp_path / "assets" / "icons" / "icon-maskable.png"

    assert icon_192.exists()
    assert icon_512.exists()
    assert icon_maskable.exists()

    with Image.open(icon_192) as img:
        assert img.size == (192, 192)
        assert img.mode == 'RGBA'
        assert img.getpixel((96, 96)) == (255, 255, 255, 255)
