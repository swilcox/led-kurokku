import json
import pytest
from datetime import datetime, time
from unittest.mock import patch, MagicMock, AsyncMock

from led_kurokku.cli.models.weather import WeatherLocation
from led_kurokku.cli.utils.weather_api import (
    fetch_openweather_data,
    format_temperature_for_display,
    get_temperature_data,
    fetch_noaa_alerts,
    process_noaa_alerts,
)


class TestWeatherAPI:
    def test_format_temperature_for_display(self):
        """Test formatting temperatures for display."""
        # Normal temperatures
        assert format_temperature_for_display(72.4) == "72*F"
        assert format_temperature_for_display(72.6) == "73*F"  # Rounds up
        assert format_temperature_for_display(0) == "0*F"
        
        # Single-digit temperatures (should have no leading space)
        assert format_temperature_for_display(5) == "5*F"
        assert format_temperature_for_display(-5) == "-5*F"
        
        # Extreme temperatures
        assert format_temperature_for_display(-10) == "LO*F"  # Below -9
        assert format_temperature_for_display(100) == "HI*F"  # Above 99
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_openweather_data_success(self, mock_get):
        """Test fetching OpenWeather data successfully."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"main": {"temp": 72}}
        
        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        result = await fetch_openweather_data("test-api-key", location)
        
        assert result == {"main": {"temp": 72}}
        mock_get.assert_called_once()
        # Check params values properly
        params = mock_get.call_args[1]["params"]
        assert params["lat"] == 0
        assert params["lon"] == 0
        assert params["appid"] == "test-api-key"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_openweather_data_error(self, mock_get):
        """Test fetching OpenWeather data with an error."""
        # Mock response with error
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Invalid API key"
        
        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        result = await fetch_openweather_data("invalid-key", location)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_openweather_data")
    async def test_get_temperature_data_success(self, mock_fetch):
        """Test getting temperature data successfully."""
        # Mock the OpenWeather data with sunrise/sunset
        mock_fetch.return_value = {
            "main": {"temp": 72},
            "sys": {
                "sunrise": 1619164800,  # Example timestamp
                "sunset": 1619213700,   # Example timestamp
            }
        }
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        temp, data, sun_data = await get_temperature_data("test-api-key", location)
        
        assert temp == "72*F"
        assert data == mock_fetch.return_value
        assert sun_data is not None
        assert isinstance(sun_data["sunrise"], time)
        assert isinstance(sun_data["sunset"], time)
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_openweather_data")
    async def test_get_temperature_data_no_sun_data(self, mock_fetch):
        """Test getting temperature data without sunrise/sunset."""
        # Mock the OpenWeather data without sunrise/sunset
        mock_fetch.return_value = {
            "main": {"temp": 72}
        }
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        temp, data, sun_data = await get_temperature_data("test-api-key", location)
        
        assert temp == "72*F"
        assert data == mock_fetch.return_value
        assert sun_data is None
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_openweather_data")
    async def test_get_temperature_data_error(self, mock_fetch):
        """Test getting temperature data with an error."""
        # Mock an error
        mock_fetch.return_value = None
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        temp, data, sun_data = await get_temperature_data("test-api-key", location)
        
        assert temp is None
        assert data is None
        assert sun_data is None
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_noaa_alerts_success(self, mock_get):
        """Test fetching NOAA alerts successfully."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Warning",
                        "expires": "2023-05-02T12:00:00Z",
                        "id": "test-id",
                        "severity": "Moderate",
                        "certainty": "Likely",
                        "urgency": "Expected",
                        "headline": "Flood Warning for Nashville",
                    }
                }
            ]
        }
        
        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        result = await fetch_noaa_alerts(location)
        
        assert len(result) == 1
        assert result[0]["properties"]["event"] == "Flood Warning"
        mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_noaa_alerts_error(self, mock_get):
        """Test fetching NOAA alerts with an error."""
        # Mock response with error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Server error"
        
        # Mock the context manager
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        result = await fetch_noaa_alerts(location)
        
        assert result == []
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_noaa_alerts")
    async def test_process_noaa_alerts_success(self, mock_fetch):
        """Test processing NOAA alerts successfully."""
        # Mock the NOAA alerts
        mock_fetch.return_value = [
            {
                "properties": {
                    "event": "Flood Warning",
                    "expires": "2023-05-02T12:00:00Z",
                    "id": "test-id",
                    "severity": "Moderate",
                    "certainty": "Likely",
                    "urgency": "Expected",
                    "headline": "Flood Warning for Nashville",
                }
            }
        ]
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        alerts = await process_noaa_alerts(location)
        
        assert len(alerts) == 1
        assert alerts[0]["message"] == "Flood Warning"
        assert alerts[0]["expires"] == "2023-05-02T12:00:00Z"
        assert alerts[0]["source"] == "NOAA"
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_noaa_alerts")
    async def test_process_noaa_alerts_no_alerts(self, mock_fetch):
        """Test processing NOAA alerts with no alerts."""
        # Mock no alerts
        mock_fetch.return_value = []
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        alerts = await process_noaa_alerts(location)
        
        assert alerts == []
    
    @pytest.mark.asyncio
    @patch("led_kurokku.cli.utils.weather_api.fetch_noaa_alerts")
    async def test_process_noaa_alerts_invalid_data(self, mock_fetch):
        """Test processing NOAA alerts with invalid data."""
        # Mock invalid data
        mock_fetch.return_value = [
            {
                "properties": {
                    # Missing required fields
                }
            }
        ]
        
        location = WeatherLocation(name="test", lat=0, lon=0)
        alerts = await process_noaa_alerts(location)
        
        assert alerts == []