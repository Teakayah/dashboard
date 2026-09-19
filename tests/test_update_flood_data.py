
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from deployment.update_flood_data import fetch_gauge_data, fetch_precip_data, main, async_main

@pytest.mark.asyncio
async def test_fetch_gauge_data_success():
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
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_data
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await fetch_gauge_data(mock_session, station_id)

    assert result == {
        "level": 59.5,
        "discharge": 1500.0,
        "datetime": "2023-10-25T14:00:00Z",
        "station_id": station_id
    }
    mock_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_gauge_data_no_features():
    station_id = "02KF005"
    mock_data = {
        "features": []
    }
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_data
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    result = await fetch_gauge_data(mock_session, station_id)

    assert result is None
    mock_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_gauge_data_error(capsys):
    station_id = "02KF005"
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Network timeout")

    result = await fetch_gauge_data(mock_session, station_id)

    assert result is None
    mock_session.get.assert_called_once()

    captured = capsys.readouterr()
    assert f"Error fetching station {station_id}: Network timeout" in captured.out



@pytest.mark.asyncio
async def test_fetch_precip_data_success():
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

    mock_resp = AsyncMock()
    mock_resp.json.return_value = mock_data
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    result = await fetch_precip_data(mock_session, climate_id)

    assert result is not None
    assert result["total_7d"] == 7.0
    assert result["latest_date"] == "2024-05-05"
    mock_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_precip_data_no_features():
    climate_id = "6106000"
    mock_data = {
        "features": []
    }
    mock_resp = AsyncMock()
    mock_resp.json.return_value = mock_data
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    result = await fetch_precip_data(mock_session, climate_id)

    assert result is None
    mock_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_precip_data_error(capsys):
    climate_id = "6106000"
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Network timeout")

    result = await fetch_precip_data(mock_session, climate_id)

    assert result is None
    mock_session.get.assert_called_once()

    captured = capsys.readouterr()
    assert "Error fetching precip data: Network timeout" in captured.out

@pytest.mark.asyncio
@patch('deployment.update_flood_data.fetch_gauge_data', new_callable=AsyncMock)
@patch('deployment.update_flood_data.fetch_precip_data', new_callable=AsyncMock)
async def test_main_success(mock_fetch_precip, mock_fetch_gauge):
    # There are 4 stations in the STATIONS list
    mock_fetch_gauge.side_effect = [{"level": 50.0}, {"level": 51.0}, {"level": 52.0}, {"level": 53.0}]
    mock_fetch_precip.return_value = {"total_7d": 10.0}

    m_open = mock_open()
    with patch('builtins.open', m_open):
        await async_main()

    m_open.assert_called_once()
    handle = m_open()

    # Reconstruct the string that was written via multiple write calls
    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
    import json
    parsed_data = json.loads(written_content)

    assert "timestamp" in parsed_data
    assert "gauges" in parsed_data
    assert len(parsed_data["gauges"]) == 4
    assert "precip" in parsed_data
    assert parsed_data["precip"]["total_7d"] == 10.0

@pytest.mark.asyncio
@patch('deployment.update_flood_data.fetch_gauge_data', new_callable=AsyncMock)
@patch('deployment.update_flood_data.fetch_precip_data', new_callable=AsyncMock)
async def test_main_partial_failure(mock_fetch_precip, mock_fetch_gauge):
    # Setup mocks where some fail
    # We have 4 stations, make one fail by returning None
    side_effects = [{"level": 50.0}, None, {"level": 55.0}, {"level": 56.0}]
    mock_fetch_gauge.side_effect = side_effects
    mock_fetch_precip.return_value = None

    m_open = mock_open()
    with patch('builtins.open', m_open):
        await async_main()

    m_open.assert_called_once()
    handle = m_open()
    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
    import json
    parsed_data = json.loads(written_content)

    assert len(parsed_data["gauges"]) == 3
    assert parsed_data["precip"] is None

def test_main_cli(capsys):
    import sys

    with patch('deployment.update_flood_data.async_main', new_callable=AsyncMock):
        with patch.object(sys, 'argv', ['update_flood_data.py']):
            # Re-importing allows the __main__ block to run if coverage doesn't catch it
            # since it's already imported, we use importlib to reload
            import importlib
            from deployment import update_flood_data
            importlib.reload(update_flood_data)
