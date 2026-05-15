import json
import pytest
import runpy
from unittest.mock import patch, MagicMock

SCRIPT_PATH = 'deployment/refresh.py'

@pytest.fixture(autouse=True)
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ''
        yield mock_run

@pytest.fixture(autouse=True)
def mock_exit():
    with patch('sys.exit', side_effect=SystemExit) as mock_exit:
        yield mock_exit

@pytest.fixture
def mock_path():
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.read_text') as mock_read_text:
        yield mock_exists, mock_read_text

@patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions'])
def test_refresh_no_updates(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({'any_updated': False})

    with pytest.raises(SystemExit):
        runpy.run_path(SCRIPT_PATH, run_name='__main__')

    mock_exit.assert_called_once_with(0)
    mock_subprocess.assert_called_once()
    assert 'update_statcan_data.py' in str(mock_subprocess.call_args[0][0])

@patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions'])
def test_refresh_with_updates(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'updated': True}]
    })

    runpy.run_path(SCRIPT_PATH, run_name='__main__')

    # sys.exit(0) should NOT be called early, and it should run to completion
    mock_exit.assert_not_called()
    assert mock_subprocess.call_count >= 5

@patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions'])
def test_refresh_missing_status_file(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = False

    with pytest.raises(SystemExit):
        runpy.run_path(SCRIPT_PATH, run_name='__main__')

    mock_exit.assert_called_once_with(1)

@patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions'])
def test_refresh_with_errors(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'error': 'Failed to fetch'}]
    })

    runpy.run_path(SCRIPT_PATH, run_name='__main__')
    mock_exit.assert_not_called()
    assert mock_subprocess.call_count >= 5

@patch('sys.argv', ['refresh.py', '--no-push', '--force-descriptions'])
def test_refresh_force_descriptions(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'updated': True}]
    })

    runpy.run_path(SCRIPT_PATH, run_name='__main__')

    # generate_descriptions.py should have been run with --force
    found = False
    for call in mock_subprocess.call_args_list:
        args = call[0][0]
        if 'generate_descriptions.py' in args[-2] and '--force' in args[-1]:
            found = True
            break
    assert found

@patch('sys.argv', ['refresh.py'])
def test_refresh_with_push_no_changes(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'updated': True}]
    })

    mock_subprocess.return_value.stdout = ''
    runpy.run_path(SCRIPT_PATH, run_name='__main__')

    # we shouldn't push anything
    for call in mock_subprocess.call_args_list:
        args = call[0][0]
        assert args[0] != 'git' or args[1] not in ['add', 'commit', 'push']

@patch('sys.argv', ['refresh.py'])
def test_refresh_with_push_changes(mock_path, mock_subprocess, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'updated': True}]
    })

    def side_effect(args, **kwargs):
        mock_result = MagicMock()
        mock_result.returncode = 0
        if args[:2] == ['git', 'status']:
            mock_result.stdout = ' M index.html'
        else:
            mock_result.stdout = ''
        return mock_result

    mock_subprocess.side_effect = side_effect

    runpy.run_path(SCRIPT_PATH, run_name='__main__')

    push_calls = [c[0][0] for c in mock_subprocess.call_args_list if c[0][0][0] == 'git' and c[0][0][1] == 'push']
    assert len(push_calls) == 1

@patch('sys.argv', ['refresh.py'])
def test_refresh_subprocess_failure(mock_path, mock_exit):
    mock_exists, mock_read_text = mock_path
    mock_exists.return_value = True
    mock_read_text.return_value = json.dumps({
        'any_updated': True,
        'tables': [{'id': '14100287', 'updated': True}]
    })

    with patch('subprocess.run') as mock_run:
        # First call fails
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        with pytest.raises(SystemExit):
            runpy.run_path(SCRIPT_PATH, run_name='__main__')

        mock_exit.assert_called_once_with(1)
