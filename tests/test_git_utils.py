from pathlib import Path
from unittest.mock import patch, MagicMock
from deployment import git_utils

def test_get_git_log_batched_empty():
    assert git_utils.get_git_log_batched([], '%ci') == {}

def test_get_git_log_batched_valid_output():
    mock_result = MagicMock()
    mock_result.stdout = "TS:2024-01-01\nindex.html\n\nTS:2023-12-31\nmain.js\n"
    with patch('subprocess.run', return_value=mock_result):
        res = git_utils.get_git_log_batched(['index.html', 'main.js'], '%ci')
        assert res == {'index.html': '2024-01-01', 'main.js': '2023-12-31'}

def test_get_git_log_batched_subprocess_exception():
    with patch('subprocess.run', side_effect=Exception('Git failed')) as mock_subprocess_run:
        res = git_utils.get_git_log_batched(['index.html'], '%ci')
        assert res == {}
        mock_subprocess_run.assert_called_once_with(
            ['git', 'log', '--format=TS:%ci', '--name-only', '--', 'index.html'],
            capture_output=True,
            text=True,
            cwd=str(git_utils.ROOT)
        )

def test_get_git_dates_batched_empty():
    assert git_utils.get_git_dates_batched([]) == {}

def test_get_git_dates_batched_relative_path(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {'test.txt': '2024-01-01T12:00:00+00:00'})
    monkeypatch.setattr(Path, 'stat', lambda self: type('obj', (object,), {'st_mtime': 1700000000})())
    res = git_utils.get_git_dates_batched([Path('test.txt')])
    assert res[git_utils.ROOT / 'test.txt'] == 'Jan 2024'

def test_get_git_dates_batched_stat_exception(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {})
    p = Path('nonexistent_for_test.txt')
    res = git_utils.get_git_dates_batched([p])
    assert res == {}

def test_get_git_commit_times_batched_invalid_int(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {'test.txt': 'not_an_int'})
    res = git_utils.get_git_commit_times_batched(['test.txt'])
    assert res == {}

def test_get_git_dates_batched_absolute_paths(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {'test.txt': '2024-01-01T12:00:00+00:00'})
    monkeypatch.setattr(Path, 'stat', lambda self: type('obj', (object,), {'st_mtime': 1700000000})())
    p_inside = git_utils.ROOT / 'test.txt'
    p_outside = Path('/tmp/some_external_file.txt')
    res = git_utils.get_git_dates_batched([p_inside, p_outside])
    assert res[p_inside] == 'Jan 2024'
    assert p_outside in res

def test_get_git_dates_batched_invalid_date(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {'test.txt': 'invalid-date'})
    res = git_utils.get_git_dates_batched([Path('test.txt')])
    assert git_utils.ROOT / 'test.txt' not in res

def test_get_batched_git_isos_empty():
    assert git_utils._get_batched_git_isos([]) == {}

def test_get_batched_git_isos_valid(monkeypatch):
    monkeypatch.setattr(git_utils, 'get_git_log_batched', lambda files, fmt: {'test.txt': '2024-01-01T12:00:00+00:00'})
    p = Path('some/path/test.txt')
    res = git_utils._get_batched_git_isos([p])
    assert res == {p: '2024-01-01T12:00:00+00:00'}

def test_get_git_commit_times_batched_empty():
    assert git_utils.get_git_commit_times_batched([]) == {}
