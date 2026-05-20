from unittest.mock import patch, MagicMock
from deployment.refresh import main, parse_args
import pytest

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh._git")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_success(mock_parse, mock_status_file, mock_git, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_args.no_push = False
    mock_args.no_descriptions = False
    mock_args.force_descriptions = False
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'
    mock_git.return_value = "changes"
    mock_run.return_value = 0

    main()
    mock_exit.assert_not_called()

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_no_status_file(mock_parse, mock_status_file, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = False
    mock_run.return_value = 0
    # Stop execution when sys.exit is called to simulate real exit
    mock_exit.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        main()
    mock_exit.assert_called_with(1)

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_no_updates(mock_parse, mock_status_file, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": false, "tables": []}'
    mock_run.return_value = 0
    mock_exit.side_effect = SystemExit(0)

    with pytest.raises(SystemExit):
        main()
    mock_exit.assert_called_with(0)

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_with_errors(mock_parse, mock_status_file, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": true, "tables": [{"id": "1", "updated": false, "error": "test error"}]}'
    mock_run.return_value = 0

    main()
    mock_exit.assert_not_called()

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh._git")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_no_push(mock_parse, mock_status_file, mock_git, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_args.no_push = True
    mock_args.no_descriptions = False
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'
    mock_run.return_value = 0

    main()
    mock_git.assert_not_called()

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh._git")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_no_git_changes(mock_parse, mock_status_file, mock_git, mock_run, mock_exit):
    mock_args = MagicMock()
    mock_args.no_push = False
    mock_args.no_descriptions = True
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'
    mock_git.return_value = ""
    mock_run.return_value = 0

    main()
    mock_git.assert_called_with("status", "--porcelain")

@patch("sys.exit")
@patch("deployment.refresh._run")
@patch("deployment.refresh._git")
@patch("deployment.refresh.STATUS_FILE")
@patch("deployment.refresh.parse_args")
def test_refresh_main_force_descriptions(mock_parse, mock_status_file, mock_git, mock_run, mock_exit):
    from deployment.refresh import DEPLOY
    mock_args = MagicMock()
    mock_args.no_push = False
    mock_args.no_descriptions = False
    mock_args.force_descriptions = True
    mock_parse.return_value = mock_args

    mock_status_file.exists.return_value = True
    mock_status_file.read_text.return_value = '{"any_updated": true, "tables": [{"id": "1", "updated": true}]}'
    mock_git.return_value = "changes"
    mock_run.return_value = 0

    main()
    mock_run.assert_any_call('python3', str(DEPLOY / 'generate_descriptions.py'), '--force')

@patch("sys.exit")
@patch("deployment.refresh.subprocess.run")
def test_helpers(mock_subprocess_run, mock_exit):
    from deployment.refresh import _header, _run, _git
    _header(1, 10, "Test Step")

    # Test _run success
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.returncode = 0
    mock_subprocess_run.return_value = mock_subprocess_result
    assert _run('echo', 'hello') == 0

    # Test _run failure (exit)
    mock_subprocess_result.returncode = 1
    mock_exit.side_effect = SystemExit(1)
    with pytest.raises(SystemExit):
        _run('echo', 'hello')

    # Test _run failure (allow_nonzero)
    mock_exit.side_effect = None
    assert _run('echo', 'hello', allow_nonzero=True) == 1

    # Test _git
    mock_subprocess_result.stdout = " test \n"
    assert _git('status') == "test"

@patch("sys.exit")
def test_script_entrypoint(mock_exit):
    import runpy
    import sys
    with patch.object(sys, "argv", ["deployment/refresh.py", "--no-push"]):
        try:
            with patch("deployment.refresh.main"):
                # We need to import playwright to avoid the system exit on `from playwright.sync_api import sync_playwright` inside `main()` if playwright is not installed, but since we mock main itself it shouldn't execute
                runpy.run_path("deployment/refresh.py", run_name="__main__")
        except SystemExit:
            pass

@patch("sys.argv", ["refresh.py", "--no-push", "--no-descriptions", "--force-descriptions"])
def test_parse_args():
    from deployment.refresh import parse_args
    args = parse_args()
    assert args.no_push is True
    assert args.no_descriptions is True
    assert args.force_descriptions is True
