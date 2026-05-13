import json
from unittest.mock import patch, MagicMock, call
import pytest
from datetime import date
import runpy

from deployment.refresh import main, parse_args, _run, _git, DEPLOY, ROOT

def test_parse_args_defaults():
    with patch('sys.argv', ['refresh.py']):
        args = parse_args()
        assert not args.no_push
        assert not args.no_descriptions
        assert not args.force_descriptions

def test_parse_args_all_flags():
    with patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions', '--force-descriptions']):
        args = parse_args()
        assert args.no_push
        assert args.no_descriptions
        assert args.force_descriptions

@patch('subprocess.run')
def test_run_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert _run('echo', 'hello') == 0
    mock_run.assert_called_once_with(('echo', 'hello'), cwd=str(ROOT))

@patch('subprocess.run')
def test_run_failure_exit(mock_run):
    mock_run.return_value = MagicMock(returncode=1)
    with pytest.raises(SystemExit) as excinfo:
        _run('false')
    assert excinfo.value.code == 1

@patch('subprocess.run')
def test_run_failure_allow_nonzero(mock_run):
    mock_run.return_value = MagicMock(returncode=1)
    assert _run('false', allow_nonzero=True) == 1

@patch('subprocess.run')
def test_git_success(mock_run):
    mock_run.return_value = MagicMock(stdout=' M some_file.py \n')
    assert _git('status', '--porcelain') == 'M some_file.py'
    mock_run.assert_called_once_with(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=str(ROOT))

@patch('subprocess.run')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_main_no_updates(mock_read_text, mock_exists, mock_run):
    # Setup args
    with patch('sys.argv', ['refresh.py']):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({"any_updated": False})

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once_with(('python3', str(DEPLOY / 'update_statcan_data.py')), cwd=str(ROOT))

@patch('subprocess.run')
@patch('pathlib.Path.exists')
def test_main_missing_status_file(mock_exists, mock_run):
    with patch('sys.argv', ['refresh.py']):
        mock_exists.return_value = False

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1
        mock_run.assert_called_once_with(('python3', str(DEPLOY / 'update_statcan_data.py')), cwd=str(ROOT))

@patch('subprocess.run')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_main_with_updates(mock_read_text, mock_exists, mock_run):
    with patch('sys.argv', ['refresh.py']):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "any_updated": True,
            "tables": [{"id": "14100287", "updated": True}]
        })

        # We need _git('status', '--porcelain') to return some changes to trigger commit/push
        # mock_run will be called multiple times.
        # Let's use side_effect to provide specific mock return values for git vs normal runs
        def subprocess_run_side_effect(args, **kwargs):
            if args[0] == 'git' and args[1] == 'status':
                return MagicMock(returncode=0, stdout=' M index.html\n')
            return MagicMock(returncode=0, stdout='')

        mock_run.side_effect = subprocess_run_side_effect

        main()

        # Verify the sequence of calls
        expected_calls = [
            call(('python3', str(DEPLOY / 'update_statcan_data.py')), cwd=str(ROOT)),
            call(('python3', str(DEPLOY / 'update_flood_data.py')), cwd=str(ROOT)),
            call(('python3', str(DEPLOY / 'rebuild_analyses.py')), cwd=str(ROOT)),
            call(('python3', str(DEPLOY / 'generate_descriptions.py')), cwd=str(ROOT)),
            call(('python3', str(DEPLOY / 'generate_index.py')), cwd=str(ROOT)),
            call(('python3', str(DEPLOY / 'generate_feed.py')), cwd=str(ROOT)),
            call(('python3', '-m', 'pytest', 'tests/', '-v', '--tb=short'), cwd=str(ROOT)),
            call(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=str(ROOT)),
            call(('git', 'add', 'employment_rate_canada.html', 'nhpi_big6_comparison.html', 'descriptions.json', 'index.html', 'feed.xml'), cwd=str(ROOT)),
            call(('git', 'commit', '-m', f'chore: weekly data refresh [{date.today().isoformat()}]'), cwd=str(ROOT)),
            call(('git', 'push', 'origin', 'dev'), cwd=str(ROOT)),
        ]
        mock_run.assert_has_calls(expected_calls, any_order=False)


@patch('subprocess.run')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_main_with_updates_no_push(mock_read_text, mock_exists, mock_run):
    with patch('sys.argv', ['refresh.py', '--no-push', '--no-descriptions']):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "any_updated": True,
            "tables": [{"id": "14100287", "updated": True}, {"id": "foo", "error": "bar"}]
        })

        mock_run.return_value = MagicMock(returncode=0)

        main()

        # Check what was NOT called
        for c in mock_run.call_args_list:
            args = c.args[0]
            if isinstance(args, list) or isinstance(args, tuple):
                if args[0] == 'git' and args[1] in ('commit', 'push'):
                    pytest.fail("Git commit/push should not be called when --no-push is set")
                if 'generate_descriptions.py' in args:
                    pytest.fail("generate_descriptions.py should not be called when --no-descriptions is set")

@patch('subprocess.run')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_main_with_updates_force_descriptions(mock_read_text, mock_exists, mock_run):
    with patch('sys.argv', ['refresh.py', '--force-descriptions']):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "any_updated": True,
            "tables": [{"id": "14100287", "updated": True}]
        })

        mock_run.return_value = MagicMock(returncode=0)

        main()

        # Check that generate_descriptions.py is called with --force
        mock_run.assert_any_call(('python3', str(DEPLOY / 'generate_descriptions.py'), '--force'), cwd=str(ROOT))

@patch('subprocess.run')
@patch('pathlib.Path.exists')
@patch('pathlib.Path.read_text')
def test_main_with_updates_no_changes_git(mock_read_text, mock_exists, mock_run):
    with patch('sys.argv', ['refresh.py']):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "any_updated": True,
            "tables": [{"id": "14100287", "updated": True}]
        })

        # Make git return empty status
        def subprocess_run_side_effect(args, **kwargs):
            if args[0] == 'git' and args[1] == 'status':
                return MagicMock(returncode=0, stdout='')
            return MagicMock(returncode=0, stdout='')

        mock_run.side_effect = subprocess_run_side_effect

        main()

        # Verify push is not called
        for c in mock_run.call_args_list:
            args = c.args[0]
            if isinstance(args, list) or isinstance(args, tuple):
                if args[0] == 'git' and args[1] in ('commit', 'push'):
                    pytest.fail("Git commit/push should not be called when git status is empty")


@patch('deployment.refresh.main')
def test_entrypoint(mock_main):
    with patch('sys.argv', ['deployment/refresh.py']):
        with patch('sys.exit'):
            # Must explicitly patch 'main' in the module globals where it is executed by runpy
            runpy.run_path('deployment/refresh.py', run_name='__main__', init_globals={'main': mock_main})
