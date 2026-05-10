import pytest
import importlib.util
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys

def load_refresh_module():
    path = Path(__file__).parent.parent / 'deployment' / 'refresh.py'
    spec = importlib.util.spec_from_file_location('refresh', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_header():
    module = load_refresh_module()
    with patch('builtins.print') as mock_print:
        module._header(1, 8, "Test Title")
        mock_print.assert_called_once()
        assert "Test Title" in mock_print.call_args[0][0]

def test_run_success():
    module = load_refresh_module()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ret = module._run('echo', 'hello')
        assert ret == 0
        mock_run.assert_called_once()
        assert 'echo' in mock_run.call_args[0][0]

def test_run_failure_aborts():
    module = load_refresh_module()
    with patch('subprocess.run') as mock_run, patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        mock_run.return_value = MagicMock(returncode=1)
        module._run('false_command')
        mock_exit.assert_called_once_with(1)
        mock_print.assert_called_once()
        assert "Command failed" in mock_print.call_args[0][0]

def test_run_failure_allow_nonzero():
    module = load_refresh_module()
    with patch('subprocess.run') as mock_run, patch('sys.exit') as mock_exit:
        mock_run.return_value = MagicMock(returncode=1)
        ret = module._run('false_command', allow_nonzero=True)
        assert ret == 1
        mock_exit.assert_not_called()

def test_git():
    module = load_refresh_module()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout='  branch_name  \n')
        ret = module._git('status')
        assert ret == 'branch_name'
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ['git', 'status']

@patch('sys.argv', ['refresh.py'])
def test_main_status_file_missing():
    module = load_refresh_module()
    with patch.object(module, '_run') as mock_run, \
         patch('pathlib.Path.exists', return_value=False), \
         patch('sys.exit', side_effect=SystemExit(1)) as mock_exit, \
         patch('builtins.print') as mock_print:

        with pytest.raises(SystemExit) as excinfo:
            module.main()

        assert excinfo.value.code == 1
        mock_run.assert_called_once()
        assert 'update_statcan_data.py' in mock_run.call_args[0][1]
        mock_exit.assert_called_once_with(1)

        print_calls = [c[0][0] for c in mock_print.call_args_list]
        assert any('Status file not found after download' in p for p in print_calls)

@patch('sys.argv', ['refresh.py'])
def test_main_no_updates():
    module = load_refresh_module()
    with patch.object(module, '_run') as mock_run, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value='{"any_updated": false}'), \
         patch('sys.exit', side_effect=SystemExit(0)) as mock_exit, \
         patch('builtins.print') as mock_print:

        with pytest.raises(SystemExit) as excinfo:
            module.main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()
        mock_exit.assert_called_once_with(0)

        print_calls = [c[0][0] for c in mock_print.call_args_list]
        assert any('Stats Canada has no new data since the last refresh' in p for p in print_calls)

@patch('sys.argv', ['refresh.py'])
def test_main_download_errors_proceeds():
    module = load_refresh_module()

    mock_status = '''{
        "any_updated": true,
        "tables": [
            {"id": "14100287", "updated": true},
            {"id": "invalid", "error": "Network timeout"}
        ]
    }'''

    with patch.object(module, '_run') as mock_run, \
         patch.object(module, '_git', return_value=''), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=mock_status), \
         patch('builtins.print') as mock_print:

        module.main()

        # 1 stats_can, 1 flood, 1 rebuild, 1 generate_descriptions, 1 generate_index, 1 generate_feed, 1 pytest = 7 runs
        # No git calls in _run because _git returned empty (no push logic executed)
        assert mock_run.call_count == 7

        print_calls = [c[0][0] for c in mock_print.call_args_list]
        assert any('Download errors for table(s):' in p for p in print_calls)
        assert any("['invalid']" in p for p in print_calls)
        assert any("Updated tables: ['14100287']" in p for p in print_calls)

@patch('sys.argv', ['refresh.py'])
def test_main_full_pipeline_success():
    module = load_refresh_module()

    mock_status = '''{
        "any_updated": true,
        "tables": [{"id": "14100287", "updated": true}]
    }'''

    with patch.object(module, '_run') as mock_run, \
         patch.object(module, '_git', return_value='M file.txt'), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=mock_status), \
         patch('builtins.print') as mock_print:

        module.main()

        # 7 normal steps + 3 git runs (add, commit, push) = 10 calls
        assert mock_run.call_count == 10

        calls = mock_run.call_args_list
        assert 'update_statcan_data.py' in calls[0][0][1]
        assert 'update_flood_data.py' in calls[1][0][1]
        assert 'rebuild_analyses.py' in calls[2][0][1]
        assert 'generate_descriptions.py' in calls[3][0][1]
        assert 'generate_index.py' in calls[4][0][1]
        assert 'generate_feed.py' in calls[5][0][1]
        assert calls[6][0] == ('python3', '-m', 'pytest', 'tests/', '-v', '--tb=short')
        assert calls[7][0][0] == 'git'
        assert calls[7][0][1] == 'add'
        assert calls[8][0][0] == 'git'
        assert calls[8][0][1] == 'commit'
        assert calls[9][0][0] == 'git'
        assert calls[9][0][1] == 'push'

        print_calls = [c[0][0] for c in mock_print.call_args_list]
        assert any('Pushed to dev' in p for p in print_calls)
        assert any('Refresh complete' in p for p in print_calls)

@patch('sys.argv', ['refresh.py', '--no-push'])
def test_main_no_push_flag():
    module = load_refresh_module()

    mock_status = '''{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'''

    with patch.object(module, '_run') as mock_run, \
         patch.object(module, '_git') as mock_git, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=mock_status), \
         patch('builtins.print') as mock_print:

        module.main()

        # Should execute all 7 pipeline steps, but NOT the 3 git steps
        assert mock_run.call_count == 7
        mock_git.assert_not_called()

        print_calls = [c[0][0] for c in mock_print.call_args_list]
        assert any('--no-push set: skipping git commit and push.' in p for p in print_calls)

@patch('sys.argv', ['refresh.py', '--no-descriptions'])
def test_main_no_descriptions_flag():
    module = load_refresh_module()

    mock_status = '''{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'''

    with patch.object(module, '_run') as mock_run, \
         patch.object(module, '_git', return_value=''), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=mock_status):

        module.main()

        # 6 steps executed (descriptions omitted)
        assert mock_run.call_count == 6

        calls = mock_run.call_args_list
        scripts_run = [c[0][1] for c in calls if len(c[0]) > 1 and isinstance(c[0][1], str)]
        assert not any('generate_descriptions.py' in s for s in scripts_run)

@patch('sys.argv', ['refresh.py', '--force-descriptions'])
def test_main_force_descriptions_flag():
    module = load_refresh_module()

    mock_status = '''{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'''

    with patch.object(module, '_run') as mock_run, \
         patch.object(module, '_git', return_value=''), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value=mock_status):

        module.main()

        # Descriptions should be run with the --force flag
        calls = mock_run.call_args_list
        desc_call = next(c for c in calls if 'generate_descriptions.py' in str(c))
        assert '--force' in desc_call[0]
