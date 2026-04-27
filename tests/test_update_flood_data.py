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
