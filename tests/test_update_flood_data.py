from unittest.mock import patch
from deployment.update_flood_data import fetch_gauge_data

def test_fetch_gauge_data_error(capsys):
    station_id = "02KF005"
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network timeout")

        result = fetch_gauge_data(station_id)

        assert result is None
        mock_urlopen.assert_called_once()

        captured = capsys.readouterr()
        assert f"Error fetching station {station_id}: Network timeout" in captured.out

import json
from deployment.update_flood_data import fetch_precip_data
from unittest.mock import MagicMock

def test_fetch_precip_data_success():
    climate_id = "6106000"
    mock_data = {
        "features": [
            {"properties": {"TOTAL_PRECIPITATION": 5.2, "LOCAL_DATE": "2024-05-01"}},
            {"properties": {"TOTAL_PRECIPITATION": 0.0, "LOCAL_DATE": "2024-05-02"}},
            {"properties": {"TOTAL_PRECIPITATION": None, "LOCAL_DATE": "2024-05-03"}},
            {"properties": {"TOTAL_PRECIPITATION": 1.3, "LOCAL_DATE": "2024-05-04"}},
            {"properties": {"TOTAL_PRECIPITATION": 0.5, "LOCAL_DATE": "2024-05-05"}},
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")

    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = fetch_precip_data(climate_id)

        assert result is not None
        assert result["total_7d"] == 7.0
        assert result["latest_date"] == "2024-05-05"
        mock_urlopen.assert_called_once()
