import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from led_kurokku_cli.models.weather import (
    WeatherLocation,
    WeatherConfig,
    get_weather_config_path,
    load_weather_config,
    save_weather_config,
)


class TestWeatherLocation:
    def test_valid_location(self):
        """Test that a valid location can be created."""
        location = WeatherLocation(
            name="nashville",
            lat=36.1627,
            lon=-86.7816,
            display_name="Nashville"
        )
        
        assert location.name == "nashville"
        assert location.lat == 36.1627
        assert location.lon == -86.7816
        assert location.display_name == "Nashville"
    
    def test_default_display_name(self):
        """Test that display_name is set from name if not provided."""
        location = WeatherLocation(
            name="nashville",
            lat=36.1627,
            lon=-86.7816
        )
        
        assert location.display_name == "Nashville"
        
        # Test with underscores
        location = WeatherLocation(
            name="new_york",
            lat=40.7128,
            lon=-74.0060
        )
        
        assert location.display_name == "New York"
    
    def test_name_validation(self):
        """Test that name validation works."""
        # Invalid names
        with pytest.raises(ValueError):
            WeatherLocation(name="", lat=36.1627, lon=-86.7816)
        
        with pytest.raises(ValueError):
            WeatherLocation(name="Nashville City", lat=36.1627, lon=-86.7816)
    
    def test_latitude_validation(self):
        """Test that latitude validation works."""
        # Valid latitudes
        WeatherLocation(name="test", lat=0, lon=0)
        WeatherLocation(name="test", lat=90, lon=0)
        WeatherLocation(name="test", lat=-90, lon=0)
        
        # Invalid latitudes
        with pytest.raises(ValueError):
            WeatherLocation(name="test", lat=91, lon=0)
        
        with pytest.raises(ValueError):
            WeatherLocation(name="test", lat=-91, lon=0)
    
    def test_longitude_validation(self):
        """Test that longitude validation works."""
        # Valid longitudes
        WeatherLocation(name="test", lat=0, lon=0)
        WeatherLocation(name="test", lat=0, lon=180)
        WeatherLocation(name="test", lat=0, lon=-180)
        
        # Invalid longitudes
        with pytest.raises(ValueError):
            WeatherLocation(name="test", lat=0, lon=181)
        
        with pytest.raises(ValueError):
            WeatherLocation(name="test", lat=0, lon=-181)


class TestWeatherConfig:
    def test_default_config(self):
        """Test that a default config can be created."""
        config = WeatherConfig()
        
        assert config.locations == []
        assert config.temperature_update_interval == 300
        assert config.alerts_update_interval == 900
        assert config.openweather_api_key is None
    
    def test_config_with_locations(self):
        """Test that a config with locations can be created."""
        location = WeatherLocation(
            name="nashville",
            lat=36.1627,
            lon=-86.7816
        )
        
        config = WeatherConfig(
            locations=[location],
            temperature_update_interval=600,
            alerts_update_interval=1800,
            openweather_api_key="test-api-key"
        )
        
        assert len(config.locations) == 1
        assert config.locations[0].name == "nashville"
        assert config.temperature_update_interval == 600
        assert config.alerts_update_interval == 1800
        assert config.openweather_api_key == "test-api-key"


class TestWeatherConfigFunctions:
    @patch("led_kurokku_cli.models.weather.Path")
    def test_get_weather_config_path(self, mock_path):
        """Test that the correct path is returned."""
        mock_path.return_value.expanduser.return_value = "/home/user"
        mock_config_dir = mock_path.return_value
        mock_config_dir.mkdir.return_value = None
        
        path = get_weather_config_path()
        
        assert path == mock_config_dir / "weather_config.json"
        mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch("led_kurokku_cli.models.weather.get_weather_config_path")
    def test_load_weather_config_no_file(self, mock_get_path):
        """Test loading config when file doesn't exist."""
        mock_path = mock_get_path.return_value
        mock_path.exists.return_value = False
        
        config = load_weather_config()
        
        assert isinstance(config, WeatherConfig)
        assert config.locations == []
    
    @patch("led_kurokku_cli.models.weather.get_weather_config_path")
    @patch("builtins.open", new_callable=mock_open, read_data='{"locations": [], "temperature_update_interval": 600}')
    def test_load_weather_config_with_file(self, mock_file, mock_get_path):
        """Test loading config from an existing file."""
        mock_path = mock_get_path.return_value
        mock_path.exists.return_value = True
        
        config = load_weather_config()
        
        assert isinstance(config, WeatherConfig)
        assert config.temperature_update_interval == 600
        mock_file.assert_called_once_with(mock_path, "r")
    
    @patch("led_kurokku_cli.models.weather.get_weather_config_path")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_weather_config(self, mock_file, mock_get_path):
        """Test saving config to file."""
        mock_path = mock_get_path.return_value
        
        config = WeatherConfig(
            locations=[
                WeatherLocation(
                    name="nashville",
                    lat=36.1627,
                    lon=-86.7816
                )
            ],
            openweather_api_key="test-api-key"
        )
        
        save_weather_config(config)
        
        mock_file.assert_called_once_with(mock_path, "w")
        mock_file().write.assert_called_once()
        
        # Check the written JSON
        written_data = mock_file().write.call_args[0][0]
        json_data = json.loads(written_data)
        assert len(json_data["locations"]) == 1
        assert json_data["locations"][0]["name"] == "nashville"
        assert json_data["openweather_api_key"] == "test-api-key"