import pytest
from pathlib import Path
from deployment import git_utils

def test_get_git_log_batched_empty():
    assert git_utils.get_git_log_batched([], '%ci') == {}

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
