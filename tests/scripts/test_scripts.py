from pathlib import Path
from unittest.mock import patch, mock_open
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

        # Test empty CSV for StopIteration
        with patch('builtins.open', mock_open(read_data='')):
            assert module._read_csv_stripped(Path("fake")) == []
        with patch('builtins.open', mock_open(read_data="")):
            assert module._read_csv_stripped(Path("empty_fake")) == []

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

def test_debug_browser_run_server():
    module = load_script_as_module('debug_browser.py', 'scripts.debug_browser')
    with patch.object(module, 'HTTPServer') as mock_server:
        module.run_server()
        mock_server.assert_called_once()
        mock_server.return_value.serve_forever.assert_called_once()

def test_debug_browser_main():
    module = load_script_as_module('debug_browser.py', 'scripts.debug_browser')
    with patch.object(module, 'threading') as mock_threading:
        with patch.object(module, 'sync_playwright') as mock_pw:
            with patch('builtins.print'):
                mock_p = mock_pw.return_value.__enter__.return_value
                mock_browser = mock_p.chromium.launch.return_value
                mock_context = mock_browser.new_context.return_value
                mock_page = mock_context.new_page.return_value
                mock_page.locator.return_value.inner_text.return_value = "Ready"

                module.main()

                mock_threading.Thread.assert_called_once_with(target=module.run_server, daemon=True)
                mock_threading.Thread.return_value.start.assert_called_once()
                mock_p.chromium.launch.assert_called_once_with(headless=True)
                mock_page.goto.assert_called_once()

def test_debug_browser_callbacks():
    module = load_script_as_module('debug_browser.py', 'scripts.debug_browser')
    with patch.object(module, 'threading'):
        with patch.object(module, 'sync_playwright') as mock_pw:
            with patch('builtins.print') as mock_print:
                mock_p = mock_pw.return_value.__enter__.return_value
                mock_browser = mock_p.chromium.launch.return_value
                mock_context = mock_browser.new_context.return_value
                mock_page = mock_context.new_page.return_value

                module.main()

                # Check that on was called for console and pageerror
                calls = mock_page.on.call_args_list
                assert len(calls) == 2
                assert calls[0][0][0] == 'console'
                assert calls[1][0][0] == 'pageerror'

                # Test the lambdas
                console_lambda = calls[0][0][1]
                error_lambda = calls[1][0][1]

                class MockMsg:
                    type = "log"
                    text = "Hello world"
                mock_msg = MockMsg()
                console_lambda(mock_msg)
                mock_print.assert_any_call("CONSOLE: [log] Hello world")

                error_lambda("Test error")
                mock_print.assert_any_call("PAGE ERROR: Test error")

def test_debug_browser_entrypoint():
    with patch('threading.Thread') as mock_thread:
        with patch('playwright.sync_api.sync_playwright') as mock_pw:
            with patch('builtins.print'):
                run_script('debug_browser.py')
                mock_thread.assert_called_once()
                mock_pw.assert_called_once()
