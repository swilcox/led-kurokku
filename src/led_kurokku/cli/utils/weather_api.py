"""
Weather API utilities for the LED-Kurokku CLI server.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

import aiohttp

from ..models.weather import WeatherLocation


logger = logging.getLogger(__name__)

# Redis key constants
REDIS_WEATHER_TEMP_KEY_PREFIX = "kurokku:weather:temp:"
REDIS_WEATHER_ALERT_KEY_PREFIX = "kurokku:alert:weather:"


async def fetch_openweather_data(
    api_key: str, location: WeatherLocation
) -> dict[str, Any] | None:
    """
    Fetch current weather data from OpenWeather API.

    Args:
        api_key: OpenWeather API key
        location: Weather location to fetch data for

    Returns:
        Dictionary of weather data or None if the request failed
    """
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": location.lat,
        "lon": location.lon,
        "appid": api_key,
        "units": "imperial",  # Use Fahrenheit
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error fetching OpenWeather data: {response.status} - {error_text}"
                    )
                    return None
    except Exception as e:
        logger.error(f"Exception fetching OpenWeather data: {e}")
        return None


def format_temperature_for_display(temp_f: float) -> str:
    """
    Format a temperature value for display on a 4-character LED display.

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Formatted 4-character string (e.g., "56*F")
    """
    # Round to nearest integer
    temp_int = round(temp_f)

    # Handle special cases
    if temp_int < -9:
        return "LO*F"
    elif temp_int > 99:
        return "HI*F"

    # Format the temperature
    return f"{temp_int:2d}*F".replace(" ", "")


async def get_temperature_data(
    api_key: str, location: WeatherLocation
) -> Tuple[Optional[str], Optional[Dict], Optional[Dict]]:
    """
    Get temperature data for a location.

    Args:
        api_key: OpenWeather API key
        location: Weather location to fetch data for

    Returns:
        Tuple of (formatted temperature string, raw weather data, sunrise/sunset data)
    """
    weather_data = await fetch_openweather_data(api_key, location)

    if not weather_data:
        return None, None, None

    try:
        temp_f = weather_data["main"]["temp"]
        formatted_temp = format_temperature_for_display(temp_f)

        # Extract sunrise and sunset times
        sun_data = None
        if (
            "sys" in weather_data
            and "sunrise" in weather_data["sys"]
            and "sunset" in weather_data["sys"]
        ):
            sunrise_timestamp = weather_data["sys"]["sunrise"]
            sunset_timestamp = weather_data["sys"]["sunset"]

            # Convert from UNIX timestamps to datetime objects
            sunrise_time = datetime.fromtimestamp(sunrise_timestamp)
            sunset_time = datetime.fromtimestamp(sunset_timestamp)

            sun_data = {"sunrise": sunrise_time.time(), "sunset": sunset_time.time()}

            logger.debug(
                f"Extracted sunrise ({sunrise_time.time()}) and sunset ({sunset_time.time()}) times for {location.name}"
            )

        return formatted_temp, weather_data, sun_data
    except KeyError:
        logger.error(f"Invalid weather data format: {weather_data}")
        return None, weather_data, None


async def fetch_noaa_alerts(location: WeatherLocation) -> List[Dict[str, Any]]:
    """
    Fetch weather alerts from NOAA API.

    Args:
        location: Weather location to fetch alerts for

    Returns:
        List of alert dictionaries
    """
    url = "https://api.weather.gov/alerts/active"
    params = {
        "point": f"{location.lat},{location.lon}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("features", [])
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error fetching NOAA alerts: {response.status} - {error_text}"
                    )
                    return []
    except Exception as e:
        logger.error(f"Exception fetching NOAA alerts: {e}")
        return []


async def process_noaa_alerts(location: WeatherLocation) -> List[Dict[str, Any]]:
    """
    Process NOAA alerts for a location.

    Args:
        location: Weather location to fetch alerts for

    Returns:
        List of processed alert dictionaries
    """
    raw_alerts = await fetch_noaa_alerts(location)
    processed_alerts = []

    for alert in raw_alerts:
        try:
            properties = alert.get("properties", {})

            if not properties:
                continue

            event = properties.get("event")
            expires_str = properties.get("expires")

            if not event or not expires_str:
                continue

            # Parse expires time
            try:
                expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                ttl_seconds = max(0, int((expires - now).total_seconds()))
            except (ValueError, TypeError):
                logger.warning(f"Invalid expires format: {expires_str}")
                ttl_seconds = 3600  # Default to 1 hour

            processed_alerts.append(
                {
                    "message": event,
                    "expires": expires_str,
                    "ttl": ttl_seconds,
                    "source": "NOAA",
                    "id": properties.get("id", ""),
                    "severity": properties.get("severity", ""),
                    "certainty": properties.get("certainty", ""),
                    "urgency": properties.get("urgency", ""),
                    "headline": properties.get("headline", ""),
                }
            )
        except Exception as e:
            logger.error(f"Error processing alert: {e}")

    return processed_alerts