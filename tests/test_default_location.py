"""
Test for default location in weather models.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from led_kurokku.cli.models.weather import WeatherLocation, WeatherConfig
from led_kurokku.cli.services.weather_service import WeatherService


def test_default_location_flag():
    """Test the default location flag."""
    # Test default value (should be False)
    location = WeatherLocation(name="test", lat=0, lon=0)
    assert location.is_default is False

    # Test explicit setting to True
    location = WeatherLocation(name="test", lat=0, lon=0, is_default=True)
    assert location.is_default is True


def test_validate_one_default_location():
    """Test that only one location can be default."""
    # No default should be okay
    config = WeatherConfig(
        locations=[
            WeatherLocation(name="location1", lat=0, lon=0),
            WeatherLocation(name="location2", lat=1, lon=1),
        ]
    )
    assert len([loc for loc in config.locations if loc.is_default]) == 0

    # One default should be okay
    config = WeatherConfig(
        locations=[
            WeatherLocation(name="location1", lat=0, lon=0, is_default=True),
            WeatherLocation(name="location2", lat=1, lon=1),
        ]
    )
    assert len([loc for loc in config.locations if loc.is_default]) == 1

    # Multiple defaults should fail
    with pytest.raises(ValidationError) as excinfo:
        WeatherConfig(
            locations=[
                WeatherLocation(name="location1", lat=0, lon=0, is_default=True),
                WeatherLocation(name="location2", lat=1, lon=1, is_default=True),
            ]
        )

    assert "Only one location can be marked as default" in str(excinfo.value)


@pytest.mark.asyncio
async def test_brightness_only_updates_for_default_location():
    """Test that brightness only updates for the default location."""
    from led_kurokku.cli.models.instance import KurokkuInstance

    # Create a config with two locations, one default and one not
    config = WeatherConfig(
        locations=[
            WeatherLocation(name="default_loc", lat=0, lon=0, is_default=True),
            WeatherLocation(name="non_default_loc", lat=1, lon=1),
        ],
        openweather_api_key="fake_key",
    )

    # Create a mock instance
    mock_instance = KurokkuInstance(name="test", host="localhost", port=6379)

    # Create a mock Redis client
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    # Mock service
    service = WeatherService(config)
    service.update_brightness_settings = AsyncMock(return_value=True)
    service.connect_to_instance = AsyncMock(return_value=mock_redis)
    service.registry.instances = [mock_instance]

    # Mock temperature data with sun data
    fake_sun_data = {
        "sunrise": MagicMock(hour=6, minute=0),
        "sunset": MagicMock(hour=18, minute=0),
    }

    with patch(
        "led_kurokku.cli.services.weather_service.get_temperature_data",
        new=AsyncMock(return_value=("20°C", {}, fake_sun_data)),
    ):
        # Update for default location
        await service.update_temperature_for_location(config.locations[0])
        # Check that update_brightness_settings was called for default location
        assert service.update_brightness_settings.called

        # Reset mock and update for non-default location
        service.update_brightness_settings.reset_mock()
        await service.update_temperature_for_location(config.locations[1])
        # Check that update_brightness_settings was NOT called for non-default location
        assert not service.update_brightness_settings.called
