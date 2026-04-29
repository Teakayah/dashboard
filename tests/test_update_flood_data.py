
import json
from unittest.mock import patch, MagicMock
from deployment.update_flood_data import fetch_gauge_data

def test_fetch_gauge_data_success():
    station_id = "02KF005"
    mock_data = {
        "features": [
            {
                "properties": {
                    "LEVEL": 59.5,
                    "DISCHARGE": 1500.0,
                    "DATETIME": "2023-10-25T14:00:00Z"
                }
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')

    with patch('urllib.request.urlopen') as mock_urlopen:
        # Mock the context manager __enter__ to return mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_gauge_data(station_id)

        assert result == {
            "level": 59.5,
            "discharge": 1500.0,
            "datetime": "2023-10-25T14:00:00Z",
            "station_id": station_id
        }
        mock_urlopen.assert_called_once()

def test_fetch_gauge_data_no_features():
    station_id = "02KF005"
    mock_data = {
        "features": []
    }
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_gauge_data(station_id)

        assert result is None
        mock_urlopen.assert_called_once()

def test_fetch_gauge_data_error(capsys):
    station_id = "02KF005"
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network timeout")

        result = fetch_gauge_data(station_id)

        assert result is None
        mock_urlopen.assert_called_once()

        captured = capsys.readouterr()
        assert f"Error fetching station {station_id}: Network timeout" in captured.out
