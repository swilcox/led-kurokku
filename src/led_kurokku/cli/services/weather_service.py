"""
Weather service for LED-Kurokku CLI server.
"""

import asyncio
import json
import logging
from datetime import datetime

import redis.asyncio as redis

from ..models.instance import KurokkuInstance, load_registry
from ..models.weather import WeatherConfig, WeatherLocation
from ..utils.weather_api import (
    REDIS_WEATHER_TEMP_KEY_PREFIX,
    REDIS_WEATHER_ALERT_KEY_PREFIX,
    get_temperature_data,
    process_noaa_alerts,
)


logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service for fetching weather data and distributing to LED-Kurokku instances.
    """

    def __init__(self, config: WeatherConfig | None = None):
        """
        Initialize the weather service.

        Args:
            config: Weather service configuration
        """
        self.config = config or WeatherConfig.load()
        self.registry = load_registry()
        self.running = False
        self.temperature_task = None
        self.alerts_task = None

    async def connect_to_instance(self, instance: KurokkuInstance) -> redis.Redis:
        """
        Connect to a Redis instance.

        Args:
            instance: Instance to connect to

        Returns:
            Redis client
        """
        return redis.Redis(
            host=instance.host,
            port=instance.port,
            db=0,
        )

    async def update_temperature_for_location(
        self, location: WeatherLocation
    ) -> str | None:
        """
        Update temperature data for a location.

        Args:
            location: Location to update

        Returns:
            Formatted temperature string or None if the update failed
        """
        if not self.config.openweather_api_key:
            logger.error("No OpenWeather API key configured")
            return None

        formatted_temp, raw_data, sun_data = await get_temperature_data(
            self.config.openweather_api_key, location
        )

        if not formatted_temp:
            logger.error(f"Failed to get temperature data for {location.display_name}")
            return None

        logger.info(f"Got temperature for {location.display_name}: {formatted_temp}")

        # Distribute to all instances
        for instance in self.registry.instances:
            try:
                client = await self.connect_to_instance(instance)
                redis_key = f"{REDIS_WEATHER_TEMP_KEY_PREFIX}{location.name}"

                # Set the temperature with a TTL of 1 hour
                await client.set(redis_key, formatted_temp, ex=3600)

                # Update brightness settings only if this is the default location and sunrise/sunset data is available
                if location.is_default and sun_data:
                    await self.update_brightness_settings(client, sun_data)
                    logger.info(f"Used {location.name} (default) for brightness settings")

                await client.aclose()

                logger.info(
                    f"Updated temperature for {location.name} on {instance.name}"
                )
            except Exception as e:
                logger.error(f"Error updating temperature on {instance.name}: {e}")

        return formatted_temp

    async def update_brightness_settings(
        self, client: redis.Redis, sun_data: dict
    ) -> bool:
        """
        Update brightness settings based on sunrise/sunset times.

        Args:
            client: Redis client
            sun_data: Dictionary containing sunrise and sunset times

        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # Get the current configuration
            config_json = await client.get("kurokku:config")
            if not config_json:
                logger.warning(
                    "No configuration found in Redis, cannot update brightness settings"
                )
                return False

            config_data = json.loads(config_json)

            # Check if the brightness settings exist
            if "brightness" not in config_data:
                logger.warning("No brightness settings in configuration")
                return False

            # Check if sunrise/sunset times have changed
            current_begin = config_data["brightness"].get("begin")
            current_end = config_data["brightness"].get("end")

            # Convert string time in config to time object for comparison
            # Format is expected to be "HH:MM:SS" or "HH:MM"
            from datetime import datetime

            def parse_time_str(time_str):
                if not time_str:
                    return None
                try:
                    if ":" in time_str:
                        if time_str.count(":") == 1:
                            time_str += ":00"  # Add seconds if not present
                        return datetime.strptime(time_str, "%H:%M:%S").time()
                    return None
                except ValueError:
                    return None

            current_begin_time = parse_time_str(current_begin)
            current_end_time = parse_time_str(current_end)

            # Format new times for config (maintaining the format used in the config)
            new_begin = sun_data["sunrise"].strftime("%H:%M:%S")
            new_end = sun_data["sunset"].strftime("%H:%M:%S")

            # Only update if the times have changed
            if (
                current_begin_time is None
                or current_end_time is None
                or abs(
                    (current_begin_time.hour - sun_data["sunrise"].hour) * 60
                    + (current_begin_time.minute - sun_data["sunrise"].minute)
                )
                >= 1
                or abs(
                    (current_end_time.hour - sun_data["sunset"].hour) * 60
                    + (current_end_time.minute - sun_data["sunset"].minute)
                )
                >= 1
            ):
                # Update the brightness settings
                config_data["brightness"]["begin"] = new_begin
                config_data["brightness"]["end"] = new_end

                # Save the updated configuration
                await client.set("kurokku:config", json.dumps(config_data))

                logger.info(
                    f"Updated brightness settings: begin={new_begin}, end={new_end}"
                )
                return True
            else:
                logger.debug(
                    "Sunrise/sunset times have not changed significantly, skipping update"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating brightness settings: {e}")
            return False

    async def update_alerts_for_location(self, location: WeatherLocation) -> list[dict]:
        """
        Update alert data for a location.

        Args:
            location: Location to update

        Returns:
            List of processed alerts
        """
        alerts = await process_noaa_alerts(location)

        if not alerts:
            logger.info(f"No alerts found for {location.display_name}")
            return []

        logger.info(f"Got {len(alerts)} alerts for {location.display_name}")

        # Distribute to all instances
        for instance in self.registry.instances:
            try:
                client = await self.connect_to_instance(instance)

                # Clear existing alerts for this location
                pattern = f"{REDIS_WEATHER_ALERT_KEY_PREFIX}{location.name}:*"
                # Get all keys matching the pattern first, then delete them
                keys_to_delete = []
                async for key in client.scan_iter(pattern):
                    keys_to_delete.append(key)

                for key in keys_to_delete:
                    await client.delete(key)

                # Set new alerts
                for i, alert in enumerate(alerts):
                    redis_key = f"{REDIS_WEATHER_ALERT_KEY_PREFIX}{location.name}:{i}"
                    await client.set(
                        redis_key,
                        json.dumps(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "message": alert["message"],
                                "priority": 1,  # Higher priority than regular alerts
                                "display_duration": (len(alert["message"]) * 0.3) + 3.0,
                                "delete_after_display": False,
                            }
                        ),
                        ex=alert["ttl"],
                    )

                await client.aclose()
                logger.info(f"Updated alerts for {location.name} on {instance.name}")
            except Exception as e:
                logger.error(f"Error updating alerts on {instance.name}: {e}")

        return alerts

    async def temperature_update_loop(self):
        """Periodically update temperature data for all locations."""
        while self.running:
            logger.info("Starting temperature update cycle")

            for location in self.config.locations:
                try:
                    await self.update_temperature_for_location(location)
                except Exception as e:
                    logger.error(f"Error updating temperature for {location.name}: {e}")

            # Wait for the next update interval
            await asyncio.sleep(self.config.temperature_update_interval)

    async def alerts_update_loop(self):
        """Periodically update alert data for all locations."""
        while self.running:
            logger.info("Starting alerts update cycle")

            for location in self.config.locations:
                try:
                    await self.update_alerts_for_location(location)
                except Exception as e:
                    logger.error(f"Error updating alerts for {location.name}: {e}")

            # Wait for the next update interval
            await asyncio.sleep(self.config.alerts_update_interval)

    async def start(self):
        """Start the weather service."""
        if self.running:
            logger.warning("Weather service is already running")
            return

        if not self.config.locations:
            logger.error("No locations configured")
            return
            
        # Check if there's a default location for brightness control
        default_locations = [loc for loc in self.config.locations if loc.is_default]
        if not default_locations:
            logger.warning("No default location configured for brightness control. Sunrise/sunset-based brightness control will be disabled.")
        else:
            logger.info(f"Using {default_locations[0].name} as default location for brightness control")

        self.running = True
        self.temperature_task = asyncio.create_task(self.temperature_update_loop())
        self.alerts_task = asyncio.create_task(self.alerts_update_loop())

        logger.info("Weather service started")

    async def stop(self):
        """Stop the weather service."""
        if not self.running:
            return

        self.running = False

        if self.temperature_task:
            self.temperature_task.cancel()
            try:
                await self.temperature_task
            except asyncio.CancelledError:
                pass

        if self.alerts_task:
            self.alerts_task.cancel()
            try:
                await self.alerts_task
            except asyncio.CancelledError:
                pass

        logger.info("Weather service stopped")


def run_weather_service(config: WeatherConfig | None = None):
    """
    Run the weather service.

    Args:
        config: Weather service configuration
    """

    async def _run():
        service = WeatherService(config)

        # Set up signal handlers
        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("Stopping weather service...")
            loop.create_task(service.stop())

        # Start the service
        await service.start()

        # Run until stopped
        while service.running:
            await asyncio.sleep(1)

    # Run the async function
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_run())
    except KeyboardInterrupt:
        logger.info("Weather service interrupted by user")
    except Exception as e:
        logger.exception(f"Error in weather service: {e}")
    finally:
        loop.close()