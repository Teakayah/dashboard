import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

def load_screenshot_module():
    path = Path(__file__).parent.parent / 'deployment' / 'screenshot.py'
    spec = importlib.util.spec_from_file_location('deployment.screenshot', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_get_git_commit_times_batched_no_paths():
    module = load_screenshot_module()
    times = module.get_git_commit_times_batched([])
    assert times == {}

def test_get_git_commit_times_batched_exception():
    module = load_screenshot_module()
    with patch('subprocess.run', side_effect=Exception("Git error")):
        times = module.get_git_commit_times_batched(['test.html'])
        assert times == {}

def test_get_git_commit_times_batched_success():
    module = load_screenshot_module()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='TS:1234567890\ntest.html\npreviews/test.png\n')
        times = module.get_git_commit_times_batched(['test.html', 'previews/test.png'])
        assert times == {'test.html': 1234567890, 'previews/test.png': 1234567890}
        assert mock_run.call_count >= 1

def test_get_git_commit_times_batched_empty_paths():
    module = load_screenshot_module()
    times = module.get_git_commit_times_batched([])
    assert times == {}

def test_get_git_commit_times_batched_subprocess_error():
    module = load_screenshot_module()
    with patch('subprocess.run') as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        times = module.get_git_commit_times_batched(['test.html'])
        assert times == {}
        mock_run.assert_called_once_with(
            ['git', 'log', '--format=TS:%ct', '--name-only', '--', 'test.html'],
            capture_output=True,
            text=True,
            cwd=str(module.ROOT)
        )

def test_get_git_commit_times_batched_empty():
    module = load_screenshot_module()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='')
        times = module.get_git_commit_times_batched(['test.html'])
        assert times == {}
        assert mock_run.call_count >= 1

def test_needs_screenshot_missing():
    module = load_screenshot_module()
    with patch('pathlib.Path.exists', return_value=False):
        assert module.needs_screenshot('test_page.html', 0, 0) is True

def test_needs_screenshot_older_preview():
    module = load_screenshot_module()
    with patch('pathlib.Path.exists', return_value=True):
        assert module.needs_screenshot('test_page.html', 100, 50) is True

def test_needs_screenshot_newer_preview():
    module = load_screenshot_module()
    with patch('pathlib.Path.exists', return_value=True):
        assert module.needs_screenshot('test_page.html', 50, 100) is False

@patch("sys.argv", ["screenshot.py"])
def test_main_no_html_files():
    module = load_screenshot_module()
    with patch('pathlib.Path.glob', return_value=[]):
        module.main()

@patch("sys.argv", ["screenshot.py"])
def test_main_all_uptodate():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'
    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=False):
        module.main()

@patch("sys.argv", ["screenshot.py"])
def test_main_playwright_missing():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen') as mock_popen, \
         patch('socket.create_connection'), \
         patch.dict('sys.modules', {'playwright.sync_api': None}), \
         pytest.raises(SystemExit) as exc_info:
        module.main()

    assert 'Playwright is not installed' in str(exc_info.value)
    mock_popen.return_value.terminate.assert_called()

@patch("sys.argv", ["screenshot.py"])
def test_main_server_fails_to_start():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen') as mock_popen, \
         patch('socket.create_connection', side_effect=OSError), \
         patch('time.sleep'), \
         pytest.raises(SystemExit) as exc_info:
        module.main()

    assert 'HTTP server did not start' in str(exc_info.value)
    mock_popen.return_value.terminate.assert_called()

@patch("sys.argv", ["screenshot.py"])
def test_main_success_flow():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_pw

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen') as mock_popen, \
         patch('socket.create_connection'), \
         patch.dict('sys.modules', {'playwright.sync_api': MagicMock(sync_playwright=mock_sync_playwright)}), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.stat') as mock_stat:

        mock_stat.return_value.st_size = 1024
        module.main()

    mock_browser.new_page.assert_called_once()
    mock_page.goto.assert_called_once()
    mock_page.screenshot.assert_called_once()
    mock_page.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_popen.return_value.terminate.assert_called()
    mock_popen.return_value.wait.assert_called()

@patch("sys.argv", ["screenshot.py"])
def test_main_screenshot_failure():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_page.screenshot.side_effect = Exception("Screenshot failed")

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_pw

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen'), \
         patch('socket.create_connection'), \
         patch.dict('sys.modules', {'playwright.sync_api': MagicMock(sync_playwright=mock_sync_playwright)}), \
         patch('pathlib.Path.mkdir'), \
         pytest.raises(SystemExit) as exc_info:
        module.main()

    assert 'Failed to screenshot: [\'test.html\']' in str(exc_info.value)

@patch("sys.argv", ["screenshot.py"])
def test_main_timeout_waiting_for_load_state():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_page.wait_for_load_state.side_effect = Exception("Timeout")

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_pw

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen'), \
         patch('socket.create_connection'), \
         patch.dict('sys.modules', {'playwright.sync_api': MagicMock(sync_playwright=mock_sync_playwright)}), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.stat') as mock_stat:

        mock_stat.return_value.st_size = 1024
        module.main()

    mock_browser.new_page.assert_called_once()
    mock_page.goto.assert_called_once()
    mock_page.screenshot.assert_called_once()
    mock_page.close.assert_called_once()

def test_needs_screenshot_force():
    module = load_screenshot_module()
    assert module.needs_screenshot('test_page.html', 0, 0, force=True) is True

def test_needs_screenshot_mtime_fallback():
    module = load_screenshot_module()
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.stat') as mock_stat:
        # html mtime > png mtime
        mock_stat.side_effect = [MagicMock(st_mtime=50), MagicMock(st_mtime=100)]
        assert module.needs_screenshot('test_page.html', 0, 0) is True

        mock_stat.side_effect = [MagicMock(st_mtime=100), MagicMock(st_mtime=50)]
        assert module.needs_screenshot('test_page.html', 0, 0) is False

@patch("sys.argv", ["screenshot.py"])
def test_main_wait_for_selector_exception():
    module = load_screenshot_module()
    mock_p = MagicMock()
    mock_p.name = 'test.html'

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page

    # Simulate wait_for_selector throwing an Exception
    mock_page.wait_for_selector.side_effect = Exception("Timeout waiting for selector")

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_pw

    with patch('pathlib.Path.glob', return_value=[mock_p]), \
         patch.object(module, 'get_git_commit_times_batched', return_value={}), \
         patch.object(module, 'needs_screenshot', return_value=True), \
         patch('subprocess.Popen') as _, \
         patch('socket.create_connection'), \
         patch.dict('sys.modules', {'playwright.sync_api': MagicMock(sync_playwright=mock_sync_playwright)}), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.stat') as mock_stat:

        mock_stat.return_value.st_size = 1024
        module.main()

    mock_page.wait_for_selector.assert_called_once()
    mock_page.wait_for_timeout.assert_not_called()
    mock_page.screenshot.assert_called_once()
