import json
from datetime import date
from unittest.mock import MagicMock, patch

from deployment.update_statcan_data import fetch_changed_since, _normalize_pid

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

def test_fetch_changed_since_error():
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("API failure")

        result = fetch_changed_since(date(2023, 1, 1))

        assert result is None
        mock_urlopen.assert_called_once()
