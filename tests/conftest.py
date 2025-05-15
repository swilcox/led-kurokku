import pytest
from unittest.mock import AsyncMock

from fakeredis import FakeAsyncRedis

from led_kurokku.cli.models.instance import KurokkuInstance, KurokkuRegistry
from led_kurokku.cli.models.weather import WeatherLocation, WeatherConfig


class AsyncIterator:
    """A proper async iterator for testing async for loops."""

    def __init__(self, items):
        self.items = items.copy() if items else []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.fixture
def fake_async_redis():
    return FakeAsyncRedis()


@pytest.fixture
def test_instances():
    """Create test instances for testing."""
    return [
        KurokkuInstance(name="instance1", host="localhost", port=6379),
        KurokkuInstance(name="instance2", host="localhost", port=6380),
    ]


@pytest.fixture
def test_registry(test_instances):
    """Create test registry with instances."""
    return KurokkuRegistry(instances=test_instances)


@pytest.fixture
def test_locations():
    """Create test weather locations."""
    return [
        WeatherLocation(name="nashville", lat=36.1627, lon=-86.7816),
        WeatherLocation(name="san_francisco", lat=37.7749, lon=-122.4194),
    ]


@pytest.fixture
def test_weather_config(test_locations):
    """Create test weather config with locations."""
    return WeatherConfig(locations=test_locations, openweather_api_key="test-api-key")


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    client = AsyncMock()
    client.get.return_value = (
        '{"brightness": {"begin": "08:00", "end": "20:00", "high": 7, "low": 2}}'
    )
    client.set.return_value = True
    client.scan_iter.return_value = AsyncIterator([])  # Use our AsyncIterator
    client.close.return_value = None
    return client
