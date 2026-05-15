import pytest
import subprocess
import sys
import json
from unittest.mock import Mock, patch
from pathlib import Path

import importlib.util

def load_refresh_module():
    spec = importlib.util.spec_from_file_location("refresh", "deployment/refresh.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "mocked stdout"
        mock_run.return_value = mock_result
        yield mock_run

@pytest.fixture
def mock_sys_exit():
    with patch('sys.exit') as mock_exit:
        mock_exit.side_effect = SystemExit
        yield mock_exit

@pytest.fixture
def mock_path():
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.read_text') as mock_read_text:

        # Default behavior: exists returns True, read_text returns valid JSON with updates
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "any_updated": True,
            "tables": [{"id": "test_table", "updated": True}]
        })

        yield mock_exists, mock_read_text

def test_header():
    module = load_refresh_module()
    # Just to ensure it doesn't crash
    module._header(1, 5, "Test Title")

def test_run_success(mock_subprocess):
    module = load_refresh_module()
    assert module._run('echo', 'hello') == 0
    mock_subprocess.assert_called_once()

def test_run_failure_no_allow_nonzero(mock_subprocess, mock_sys_exit):
    module = load_refresh_module()
    mock_subprocess.return_value.returncode = 1

    with pytest.raises(SystemExit):
        module._run('false')

    mock_sys_exit.assert_called_once_with(1)

def test_run_failure_allow_nonzero(mock_subprocess, mock_sys_exit):
    module = load_refresh_module()
    mock_subprocess.return_value.returncode = 1

    # Should not exit
    assert module._run('false', allow_nonzero=True) == 1
    mock_sys_exit.assert_not_called()

def test_git_success(mock_subprocess):
    module = load_refresh_module()
    mock_subprocess.return_value.stdout = "  git output  \n"

    assert module._git('status') == "git output"
    mock_subprocess.assert_called_once()

def test_main_success_all_steps(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    mock_subprocess.return_value.stdout = "M file1.html" # simulate git changes

    module.main()

    # Verify that python commands were called
    calls = [c.args[0][0] for c in mock_subprocess.call_args_list]
    assert 'python3' in calls
    assert 'git' in calls
    mock_sys_exit.assert_not_called()

def test_main_no_push(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py', '--no-push'])

    module.main()

    # Verify git push was not called
    for call in mock_subprocess.call_args_list:
        args = call.args[0]
        if args[0] == 'git':
            assert args[1] != 'push'

def test_main_no_descriptions(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py', '--no-descriptions'])

    module.main()

    # Verify generate_descriptions was not called
    for call in mock_subprocess.call_args_list:
        args = call.args[0]
        if args[0] == 'python3':
            assert 'generate_descriptions.py' not in args[1]

def test_main_force_descriptions(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py', '--force-descriptions'])

    module.main()

    # Verify --force was passed
    found = False
    for call in mock_subprocess.call_args_list:
        args = call.args[0]
        if args[0] == 'python3' and 'generate_descriptions.py' in args[1]:
            assert '--force' in args
            found = True
    assert found

def test_main_status_file_missing(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    mock_exists, _ = mock_path
    mock_exists.return_value = False

    with pytest.raises(SystemExit):
        module.main()

    mock_sys_exit.assert_called_once_with(1)

def test_main_no_new_data(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    _, mock_read_text = mock_path
    mock_read_text.return_value = json.dumps({"any_updated": False})

    with pytest.raises(SystemExit):
        module.main()

    mock_sys_exit.assert_called_once_with(0)

def test_main_download_errors(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    _, mock_read_text = mock_path
    mock_read_text.return_value = json.dumps({
        "any_updated": True,
        "tables": [{"id": "test_table", "error": "timeout"}, {"id": "test_table2", "updated": True}]
    })

    # Should complete execution even with download errors
    module.main()
    mock_sys_exit.assert_not_called()

def test_main_no_git_changes(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    module = load_refresh_module()
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    def mock_run_side_effect(args, **kwargs):
        mock_result = Mock()
        mock_result.returncode = 0
        if args[0] == 'git' and args[1] == 'status':
            mock_result.stdout = "" # No changes
        else:
            mock_result.stdout = "output"
        return mock_result

    mock_subprocess.side_effect = mock_run_side_effect

    module.main()

    # Verify git push was not called
    for call in mock_subprocess.call_args_list:
        args = call.args[0]
        if args[0] == 'git':
            assert args[1] != 'push'

def test_if_name_main(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    import runpy
    monkeypatch.setattr(sys, 'argv', ['refresh.py'])

    # We shouldn't patch deployment.refresh.main since runpy executes a separate namespace
    # We can just verify it completes and calls our mocked subprocess
    runpy.run_path('deployment/refresh.py', run_name='__main__')

    # Verify git was called which implies main ran
    git_called = False
    for call in mock_subprocess.call_args_list:
        if call.args[0][0] == 'git':
            git_called = True
    assert git_called
