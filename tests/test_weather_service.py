import json
import pytest
import asyncio
from datetime import datetime, time
from unittest.mock import patch, MagicMock, AsyncMock
from fakeredis import FakeAsyncRedis

from led_kurokku.cli.models.instance import KurokkuInstance, KurokkuRegistry
from led_kurokku.cli.models.weather import WeatherLocation, WeatherConfig
from led_kurokku.cli.services.weather_service import WeatherService


class TestWeatherService:
    def setup_method(self):
        """Set up test fixtures."""
        # Create test instances
        self.instance1 = KurokkuInstance(name="instance1", host="localhost", port=6379)
        self.instance2 = KurokkuInstance(name="instance2", host="localhost", port=6380)

        # Create test registry
        self.registry = KurokkuRegistry(instances=[self.instance1, self.instance2])

        # Create test locations
        self.location1 = WeatherLocation(
            name="nashville", lat=36.1627, lon=-86.7816, is_default=True
        )
        self.location2 = WeatherLocation(
            name="san_francisco", lat=37.7749, lon=-122.4194
        )

        # Create test config
        self.config = WeatherConfig(
            locations=[self.location1, self.location2],
            openweather_api_key="test-api-key",
        )

    @pytest.mark.asyncio
    @patch("led_kurokku.cli.services.weather_service.load_registry")
    async def test_init(self, mock_load_registry):
        """Test initializing the weather service."""
        mock_load_registry.return_value = self.registry

        service = WeatherService(self.config)

        assert service.config == self.config
        assert service.registry == self.registry
        assert not service.running
        assert service.temperature_task is None
        assert service.alerts_task is None

    @pytest.mark.asyncio
    @patch("redis.asyncio.Redis")
    async def test_connect_to_instance(self, mock_redis):
        """Test connecting to a Redis instance."""
        mock_redis.return_value = AsyncMock()
        service = WeatherService(self.config)

        client = await service.connect_to_instance(self.instance1)

        mock_redis.assert_called_once_with(
            host=self.instance1.host, port=self.instance1.port, db=0
        )

    @pytest.mark.asyncio
    @patch("led_kurokku.cli.services.weather_service.get_temperature_data")
    @patch(
        "led_kurokku.cli.services.weather_service.WeatherService.connect_to_instance"
    )
    async def test_update_temperature_for_location(self, mock_connect, mock_get_temp):
        """Test updating temperature data for a location."""
        # Mock the temperature data
        mock_get_temp.return_value = ("72*F", {"main": {"temp": 72}}, None)

        # Mock the Redis client
        mock_client = AsyncMock()
        mock_connect.return_value = mock_client

        service = WeatherService(self.config)
        service.registry = self.registry

        result = await service.update_temperature_for_location(self.location1)

        assert result == "72*F"
        mock_get_temp.assert_called_once_with(
            self.config.openweather_api_key, self.location1
        )

        # Check Redis calls (should be once per instance)
        assert mock_connect.call_count == len(self.registry.instances)
        assert mock_client.set.call_count == len(self.registry.instances)

        # Check the Redis key and value
        redis_key = f"kurokku:weather:temp:{self.location1.name}"
        mock_client.set.assert_called_with(redis_key, "72*F", ex=3600)

    @pytest.mark.asyncio
    @patch("led_kurokku.cli.services.weather_service.get_temperature_data")
    @patch(
        "led_kurokku.cli.services.weather_service.WeatherService.connect_to_instance"
    )
    @patch(
        "led_kurokku.cli.services.weather_service.WeatherService.update_brightness_settings"
    )
    async def test_update_temperature_with_sun_data(
        self, mock_update_brightness, mock_connect, mock_get_temp
    ):
        """Test updating temperature with sun data."""
        # Mock the temperature data with sun data
        sun_data = {"sunrise": time(5, 0), "sunset": time(19, 0)}
        mock_get_temp.return_value = ("72*F", {"main": {"temp": 72}}, sun_data)

        # Mock the Redis client
        mock_client = AsyncMock()
        mock_connect.return_value = mock_client

        service = WeatherService(self.config)
        service.registry = self.registry

        result = await service.update_temperature_for_location(self.location1)

        assert result == "72*F"

        # Check that update_brightness_settings was called
        assert mock_update_brightness.call_count == len(self.registry.instances)
        mock_update_brightness.assert_called_with(mock_client, sun_data)

    @pytest.mark.asyncio
    @patch(
        "led_kurokku.cli.services.weather_service.WeatherService.connect_to_instance"
    )
    async def test_update_brightness_settings_success(self, mock_connect):
        """Test updating brightness settings successfully."""
        # Mock the Redis client
        mock_client = AsyncMock()
        mock_client.get.return_value = json.dumps(
            {
                "brightness": {
                    "begin": "08:00:00",
                    "end": "20:00:00",
                    "high": 7,
                    "low": 2,
                }
            }
        )
        mock_connect.return_value = mock_client

        service = WeatherService(self.config)

        sun_data = {"sunrise": time(6, 0), "sunset": time(18, 0)}

        result = await service.update_brightness_settings(mock_client, sun_data)

        assert result is True

        # Check that Redis get and set were called
        mock_client.get.assert_called_once_with("kurokku:config")
        mock_client.set.assert_called_once()

        # Check the updated config
        updated_config = json.loads(mock_client.set.call_args[0][1])
        assert updated_config["brightness"]["begin"] == "06:00:00"
        assert updated_config["brightness"]["end"] == "18:00:00"

    @pytest.mark.asyncio
    @patch(
        "led_kurokku.cli.services.weather_service.WeatherService.connect_to_instance"
    )
    async def test_update_brightness_settings_no_change(self, mock_connect):
        """Test that brightness settings aren't updated if times haven't changed significantly."""
        # Mock the Redis client with config that matches the sun data
        mock_client = AsyncMock()
        mock_client.get.return_value = json.dumps(
            {
                "brightness": {
                    "begin": "06:00:00",
                    "end": "18:00:00",
                    "high": 7,
                    "low": 2,
                }
            }
        )
        mock_connect.return_value = mock_client

        service = WeatherService(self.config)

        sun_data = {
            "sunrise": time(6, 0, 1),  # Only 1 second different
            "sunset": time(18, 0, 1),  # Only 1 second different
        }

        result = await service.update_brightness_settings(mock_client, sun_data)

        assert result is False

        # Check that Redis get was called but set was not
        mock_client.get.assert_called_once_with("kurokku:config")
        mock_client.set.assert_not_called()

    @pytest.mark.asyncio
    @patch("led_kurokku.cli.services.weather_service.process_noaa_alerts")
    @patch("redis.asyncio.Redis", new_callable=lambda: FakeAsyncRedis)
    async def test_update_alerts_for_location(self, mock_redis, mock_process_alerts):
        """Test updating alerts for a location."""
        # Mock the alerts data
        mock_alerts = [
            {
                "message": "Flood Warning",
                "expires": "2023-05-02T12:00:00Z",
                "ttl": 3600,
                "source": "NOAA",
                "id": "test-id",
                "severity": "Moderate",
            }
        ]
        mock_process_alerts.return_value = mock_alerts

        # We're using FakeAsyncRedis which has proper async support
        # Use a counter to track Redis instantiations
        original_init = FakeAsyncRedis.__init__
        instantiation_count = 0

        def count_instantiations(obj, *args, **kwargs):
            nonlocal instantiation_count
            instantiation_count += 1
            return original_init(obj, *args, **kwargs)

        # Patch the init method to count instantiations
        FakeAsyncRedis.__init__ = count_instantiations

        service = WeatherService(self.config)
        service.registry = self.registry

        try:
            alerts = await service.update_alerts_for_location(self.location1)

            assert len(alerts) == 1
            assert alerts[0]["message"] == "Flood Warning"

            mock_process_alerts.assert_called_once_with(self.location1)

            # Check that Redis clients were created
            assert instantiation_count > 0
        finally:
            # Restore the original init method
            FakeAsyncRedis.__init__ = original_init

    # @pytest.mark.asyncio
    # async def test_start_service(self):
    #     """Test just starting the service (simplified test to avoid mocking async tasks)."""
    #     with patch("asyncio.create_task") as mock_create_task:
    #         service = WeatherService(self.config)

    #         # We'll just test the start functionality
    #         await service.start()

    #         assert service.running is True
    #         assert mock_create_task.call_count == 2  # One for temperature and one for alerts
