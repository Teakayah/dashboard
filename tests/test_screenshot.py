import importlib.util
from pathlib import Path
from unittest.mock import patch

def load_screenshot_module():
    path = Path(__file__).parent.parent / 'deployment' / 'screenshot.py'
    spec = importlib.util.spec_from_file_location('screenshot', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_needs_screenshot_missing_preview():
    module = load_screenshot_module()

    with patch('pathlib.Path.exists', return_value=False):
        assert module.needs_screenshot('test_page.html') is True

def test_needs_screenshot_older_preview():
    module = load_screenshot_module()

    with patch('pathlib.Path.exists', return_value=True):
        with patch.object(module, '_git_commit_time', side_effect=[100, 50]):
            assert module.needs_screenshot('test_page.html') is True

def test_needs_screenshot_newer_preview():
    module = load_screenshot_module()

    with patch('pathlib.Path.exists', return_value=True):
        with patch.object(module, '_git_commit_time', side_effect=[50, 100]):
            assert module.needs_screenshot('test_page.html') is False
