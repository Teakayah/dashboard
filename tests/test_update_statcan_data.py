import json
from datetime import date
from unittest.mock import MagicMock, patch

from deployment.update_statcan_data import fetch_changed_since, _get_end_period, _normalize_pid, _load_last_checked
import csv

def test_normalize_pid():
    # 10-digit IDs ending in '01'
    assert _normalize_pid('1010001501') == '10100015'
    assert _normalize_pid(1010001501) == '10100015'

    # 10-digit IDs not ending in '01'
    assert _normalize_pid('1010001502') == '1010001502'

    # Normal 8-digit IDs
    assert _normalize_pid('10100015') == '10100015'
    assert _normalize_pid(10100015) == '10100015'

    # Inputs with leading/trailing whitespaces
    assert _normalize_pid(' 1010001501 ') == '10100015'
    assert _normalize_pid(' 10100015 ') == '10100015'

    # Other lengths/strings
    assert _normalize_pid('short') == 'short'
    assert _normalize_pid('thisiswaytoolong') == 'thisiswaytoolong'
    assert _normalize_pid('10100015010') == '10100015010'

def test_fetch_changed_since_success():
    # Mock data returned by Stats Canada API
    mock_payload = [
        {"productId": "1010001501"},
        {"productId": "1410028701"},
        {"productId": "9999999901"}, # Not in our (mocked) _OUR_IDS
    ]

    with patch('urllib.request.urlopen') as mock_urlopen, \
         patch('deployment.update_statcan_data._OUR_IDS', {"10100015", "14100287"}):
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
