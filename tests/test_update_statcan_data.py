import csv
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from deployment.update_statcan_data import (
    _get_end_period,
    _load_last_checked,
    _normalize_pid,
    fetch_changed_since,
)


@pytest.mark.parametrize("raw_pid,expected", [
    ('1010001501', '10100015'),
    (1010001501, '10100015'),
    ('1010001502', '1010001502'),
    ('10100015', '10100015'),
    (10100015, '10100015'),
    (' 1010001501 ', '10100015'),
    (' 10100015 ', '10100015'),
    ('short', 'short'),
    ('thisiswaytoolong', 'thisiswaytoolong'),
    ('10100015010', '10100015010'),
    ('10-10-0015-01', '10100015'),
    ('10-10-0015', '10100015'),
])
def test_normalize_pid(raw_pid, expected):
    assert _normalize_pid(raw_pid) == expected

def test_fetch_changed_since_success():
    # Mock data returned by Stats Canada API
    mock_payload = [
        {"productId": "1010001501"},
        {"productId": "1410028701"},
        {"productId": "9999999901"}, # Not in our (mocked) _OUR_IDS
    ]

    with patch('urllib.request.urlopen') as mock_urlopen, \
         patch('deployment.update_statcan_data.OUR_IDS', {"10100015", "14100287"}):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_payload).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = fetch_changed_since(date(2023, 1, 1))

        assert result == {"10100015", "14100287"}
        mock_urlopen.assert_called_once()

def test_fetch_changed_since_error(capsys):
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("API failure")

        result = fetch_changed_since(date(2023, 1, 1))

        assert result is None
        mock_urlopen.assert_called_once()
        captured = capsys.readouterr()
        assert "WARNING: changed-cubes API call failed (API failure) — will download all." in captured.out

def test_fetch_changed_since_url_error(capsys):
    from urllib.error import URLError
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = URLError("Network unreachable")

        result = fetch_changed_since(date(2023, 1, 1))

        assert result is None
        mock_urlopen.assert_called_once()
        captured = capsys.readouterr()
        assert "WARNING: changed-cubes API call failed (<urlopen error Network unreachable>) — will download all." in captured.out

def test_fetch_changed_since_insecure_url():
    from deployment.update_statcan_data import fetch_changed_since
    with patch('deployment.update_statcan_data._CHANGED_URL', 'ftp://example.com/{date}'):
        with pytest.raises(ValueError, match="Insecure URL scheme"):
            fetch_changed_since(date(2023, 1, 1))

def test_download_table_insecure_url(tmp_path):
    from deployment.update_statcan_data import download_table
    table = {'id': '12345678', 'desc': 'Test Table', 'path': tmp_path / '12345678'}
    with patch('deployment.update_statcan_data._DL_URL', 'file:///etc/passwd/{pid}'):
        with pytest.raises(ValueError, match="Insecure URL scheme"):
            download_table(table)

def test_fetch_changed_since_invalid_json():
    """Test that invalid JSON from Stats Canada API returns None."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b'invalid json'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = fetch_changed_since(date(2023, 1, 1))

        assert result is None
        mock_urlopen.assert_called_once()


def test_get_end_period_missing_file(tmp_path):
    missing_file = tmp_path / "nonexistent.csv"
    assert _get_end_period(missing_file) is None


def test_get_end_period_success(tmp_path):
    csv_file = tmp_path / "metadata.csv"
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Some Column', 'End Reference Period', 'Another Column'])
        writer.writeheader()
        writer.writerow({'Some Column': 'A', 'End Reference Period': ' 2023-10 ', 'Another Column': 'B'})

    result = _get_end_period(csv_file)
    assert result == '2023-10'


def test_get_end_period_missing_column(tmp_path):
    csv_file = tmp_path / "metadata.csv"
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Some Column', 'Another Column'])
        writer.writeheader()
        writer.writerow({'Some Column': 'A', 'Another Column': 'B'})

    assert _get_end_period(csv_file) is None


def test_get_end_period_empty_file(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.touch()
    assert _get_end_period(csv_file) is None


def test_get_end_period_exception(tmp_path):
    # Pass a directory path where a file is expected, causing an exception when opening/reading
    assert _get_end_period(tmp_path) is None


def test_get_end_period_invalid_csv(tmp_path):
    csv_file = tmp_path / "invalid.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("This is just some text, not a CSV, and it lacks the correct headers\n")
    assert _get_end_period(csv_file) is None


def test_load_last_checked_missing_file(tmp_path):
    with patch('deployment.update_statcan_data.STATUS_FILE', tmp_path / "missing.json"):
        assert _load_last_checked() is None


def test_load_last_checked_success(tmp_path):
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({'last_checked_date': '2023-11-15'}))
    with patch('deployment.update_statcan_data.STATUS_FILE', status_file):
        assert _load_last_checked() == date(2023, 11, 15)


def test_load_last_checked_invalid_json(tmp_path):
    status_file = tmp_path / "status.json"
    status_file.write_text("invalid json")
    with patch('deployment.update_statcan_data.STATUS_FILE', status_file):
        assert _load_last_checked() is None


def test_load_last_checked_missing_key(tmp_path):
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({'some_other_key': '2023-11-15'}))
    with patch('deployment.update_statcan_data.STATUS_FILE', status_file):
        assert _load_last_checked() is None


def test_load_last_checked_invalid_date(tmp_path):
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({'last_checked_date': 'not-a-date'}))
    with patch('deployment.update_statcan_data.STATUS_FILE', status_file):
        assert _load_last_checked() is None

@patch('deployment.update_statcan_data._get_end_period')
@patch('zipfile.ZipFile')
@patch('urllib.request.urlopen')
def test_download_table_success(mock_urlopen, mock_zipfile, mock_get_end_period, tmp_path):
    from deployment.update_statcan_data import download_table
    table = {'id': '12345678', 'desc': 'Test Table', 'path': tmp_path / '12345678'}
    mock_get_end_period.side_effect = ['2023-01', '2023-02']

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"dummy zip data"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    result = download_table(table)

    assert result == {
        'id': '12345678',
        'desc': 'Test Table',
        'prev_end': '2023-01',
        'new_end': '2023-02',
        'updated': True
    }

@patch('deployment.update_statcan_data._get_end_period')
@patch('urllib.request.urlopen')
def test_download_table_bad_zip(mock_urlopen, mock_get_end_period, tmp_path):
    from deployment.update_statcan_data import download_table
    table = {'id': '12345678', 'desc': 'Test Table', 'path': tmp_path / '12345678'}
    mock_get_end_period.return_value = '2023-01'

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"invalid zip data"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    result = download_table(table)

    assert result['id'] == '12345678'
    assert 'File is not a zip file' in result['error']
    assert result['updated'] is False
    assert result['prev_end'] == '2023-01'

@patch('deployment.update_statcan_data._get_end_period')
@patch('urllib.request.urlopen')
def test_download_table_network_error(mock_urlopen, mock_get_end_period, tmp_path):
    from deployment.update_statcan_data import download_table
    table = {'id': '12345678', 'desc': 'Test Table', 'path': tmp_path / '12345678'}
    mock_get_end_period.return_value = '2023-01'

    mock_urlopen.side_effect = Exception("Network connection lost")

    result = download_table(table)

    assert result['id'] == '12345678'
    assert 'Network connection lost' in result['error']
    assert result['updated'] is False
    assert result['prev_end'] == '2023-01'

def test_write_status_success(tmp_path):
    from datetime import datetime, timezone

    from deployment.update_statcan_data import _write_status
    now = datetime.now(timezone.utc)
    today = date.today()
    tables = [{'id': '123'}]

    mock_status_file = tmp_path / 'status.json'

    with patch('deployment.update_statcan_data.STATUS_FILE', mock_status_file), \
         patch('deployment.update_statcan_data.ROOT', tmp_path):
        _write_status(now, today, True, tables)

        status = json.loads(mock_status_file.read_text())
        assert status['any_updated'] is True
        assert status['tables'] == tables
        assert status['last_checked_date'] == today.isoformat()

@patch('deployment.update_statcan_data._load_last_checked')
@patch('deployment.update_statcan_data.TABLES', [{'id': '123', 'desc': 'T'}])
def test_main_first_run(mock_load, capsys):
    from deployment.update_statcan_data import main
    mock_load.return_value = None
    with patch('deployment.update_statcan_data.download_table') as mock_dl:
        mock_dl.return_value = {'id': '123', 'desc': 'T', 'updated': True}
        with patch('deployment.update_statcan_data._write_status') as mock_ws:
            result = main()
            assert result == 1
            mock_dl.assert_called_once()
            mock_ws.assert_called_once()
            assert 'First run — downloading all tables.' in capsys.readouterr().out

@patch('deployment.update_statcan_data._load_last_checked')
@patch('deployment.update_statcan_data.TABLES', [{'id': '123', 'desc': 'T'}])
def test_main_max_lookback(mock_load, capsys):
    from deployment.update_statcan_data import main
    mock_load.return_value = date.today() - timedelta(days=61)
    with patch('deployment.update_statcan_data.download_table') as mock_dl:
        mock_dl.return_value = {'id': '123', 'desc': 'T', 'updated': True}
        with patch('deployment.update_statcan_data._write_status') as mock_ws:
            result = main()
            assert result == 1
            mock_dl.assert_called_once()
            mock_ws.assert_called_once()
            assert 'Downloading all tables to be safe.' in capsys.readouterr().out

@patch('deployment.update_statcan_data._load_last_checked')
@patch('deployment.update_statcan_data.TABLES', [{'id': '123', 'desc': 'T'}])
@patch('deployment.update_statcan_data.fetch_changed_since')
def test_main_api_failure(mock_fetch, mock_load, capsys):
    from deployment.update_statcan_data import main
    mock_load.return_value = date.today() - timedelta(days=10)
    mock_fetch.return_value = None
    with patch('deployment.update_statcan_data.download_table') as mock_dl:
        mock_dl.return_value = {'id': '123', 'desc': 'T', 'updated': False}
        with patch('deployment.update_statcan_data._write_status') as mock_ws:
            result = main()
            assert result == 0
            mock_dl.assert_called_once()
            mock_ws.assert_called_once()

@patch('deployment.update_statcan_data._load_last_checked')
@patch('deployment.update_statcan_data.TABLES', [{'id': '123', 'desc': 'T'}])
@patch('deployment.update_statcan_data.fetch_changed_since')
def test_main_no_updates(mock_fetch, mock_load, capsys):
    from deployment.update_statcan_data import main
    mock_load.return_value = date.today() - timedelta(days=10)
    mock_fetch.return_value = set()
    with patch('deployment.update_statcan_data._write_status') as mock_ws:
        result = main()
        assert result == 0
        mock_ws.assert_called_once()
        assert 'No updates for our tables. Nothing to download.' in capsys.readouterr().out

@patch('deployment.update_statcan_data._load_last_checked')
@patch('deployment.update_statcan_data.TABLES', [{'id': '123', 'desc': 'T1'}, {'id': '456', 'desc': 'T2'}])
@patch('deployment.update_statcan_data.fetch_changed_since')
def test_main_partial_updates(mock_fetch, mock_load, capsys):
    from deployment.update_statcan_data import main
    mock_load.return_value = date.today() - timedelta(days=10)
    mock_fetch.return_value = {'123'}
    with patch('deployment.update_statcan_data.download_table') as mock_dl:
        mock_dl.return_value = {'id': '123', 'desc': 'T1', 'updated': True, 'error': 'err'}
        with patch('deployment.update_statcan_data._write_status') as mock_ws:
            result = main()
            assert result == 1
            mock_dl.assert_called_once()
            mock_ws.assert_called_once()
            out = capsys.readouterr().out
            assert "Skipping unchanged: ['456']" in out
            assert "Errors (1): ['123']" in out

def test_download_table_no_change(tmp_path, monkeypatch):
    import io
    import sys
    import zipfile
    from unittest.mock import MagicMock

    from deployment import update_statcan_data
    monkeypatch.setattr(update_statcan_data, 'ROOT', tmp_path)

    table = {
        'id': '10100015',
        'desc': 'Test Table',
        'url': 'https://example.com/data.zip',
        'zip_name': '10100015.csv',
        'csv_name': 'test.csv',
        'path': tmp_path
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('10100015.csv', 'some csv data')

    mock_resp = MagicMock()
    mock_resp.read.return_value = buffer.getvalue()

    from unittest.mock import patch
    with patch('deployment.update_statcan_data.urllib.request.urlopen') as mock_urllib_open:
        mock_urllib_open.return_value.__enter__.return_value = mock_resp
        with patch('deployment.update_statcan_data._get_end_period') as mock_get_end_period:
            mock_get_end_period.side_effect = ['2023-01', '2023-01']

            captured_output = io.StringIO()
            monkeypatch.setattr(sys, 'stdout', captured_output)

            result = update_statcan_data.download_table(table)

            assert "No change" in captured_output.getvalue()
            assert not result['updated']
            assert result['prev_end'] == '2023-01'
            assert result['new_end'] == '2023-01'


@patch('deployment.update_statcan_data._get_end_period')
def test_download_table_path_traversal(mock_get_end_period, tmp_path):
    import io
    import zipfile

    from deployment.update_statcan_data import download_table
    table = {'id': '12345678', 'desc': 'Test Table', 'path': tmp_path / '12345678'}
    mock_get_end_period.return_value = '2023-01'

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr('../malicious.csv', 'some csv data')

    mock_resp = MagicMock()
    mock_resp.read.return_value = buffer.getvalue()

    with patch('deployment.update_statcan_data.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = download_table(table)

    assert result['id'] == '12345678'
    assert 'Path traversal attempt detected in ZIP' in result['error']
    assert result['updated'] is False
    assert result['prev_end'] == '2023-01'
