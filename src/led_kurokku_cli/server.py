"""
Weather fetching server for LED-Kurokku displays.

This module will be developed further to fetch weather data and send it to LED-Kurokku displays.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
import json
import time

import click

from .models.instance import load_registry
from .utils.redis_helpers import connect_to_instance, send_alert


logger = logging.getLogger(__name__)


async def fetch_weather(api_key, location):
    """
    Placeholder for fetching weather data from an API.
    
    This will be implemented to fetch real weather data in the future.
    """
    # Placeholder implementation
    return {
        "temperature": 23.5,
        "condition": "Sunny",
        "timestamp": datetime.now().isoformat()
    }


async def weather_service(registry_name, interval, api_key, location):
    """
    Service that periodically fetches weather data and sends it to an instance.
    """
    registry = load_registry()
    instance = registry.get_instance(registry_name)
    
    if not instance:
        logger.error(f"No instance found with name '{registry_name}'.")
        return
    
    logger.info(f"Starting weather service for instance '{registry_name}'.")
    logger.info(f"Fetching weather data every {interval} seconds.")
    
    while True:
        try:
            # Fetch weather data
            weather_data = await fetch_weather(api_key, location)
            
            # Format a message
            temp = weather_data.get("temperature", "N/A")
            condition = weather_data.get("condition", "Unknown")
            message = f"{temp}°C {condition}"
            
            # Send an alert with the weather data
            await send_alert(
                instance,
                message,
                ttl=interval * 2,  # TTL is twice the interval
                display_duration=5.0,
                priority=10,  # Low priority (higher numbers = lower priority)
            )
            
            logger.info(f"Sent weather update: {message}")
        except Exception as e:
            logger.error(f"Error in weather service: {e}")
        
        # Wait for the next interval
        await asyncio.sleep(interval)


def run_weather_service(instance_name, interval=1800, api_key=None, location=None):
    """
    Run the weather service.
    
    Args:
        instance_name: The name of the instance to send weather data to.
        interval: The interval in seconds between weather updates.
        api_key: The API key for the weather service.
        location: The location to fetch weather data for.
    """
    logger.info("Starting weather service...")
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received signal, shutting down...")
        loop.stop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start the weather service
    try:
        loop.run_until_complete(weather_service(instance_name, interval, api_key, location))
    except Exception as e:
        logger.exception(f"Error in weather service: {e}")
    finally:
        logger.info("Weather service stopped.")


# CLI command for starting the server
@click.command()
@click.argument("instance_name")
@click.option("--interval", "-i", default=1800, help="Interval in seconds between weather updates (default: 1800)")
@click.option("--api-key", "-k", help="API key for the weather service")
@click.option("--location", "-l", help="Location to fetch weather data for")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def start_server(instance_name, interval, api_key, location, debug):
    """
    Start the weather fetching server.
    
    This server fetches weather data and sends it to the specified LED-Kurokku instance.
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Validate arguments
    registry = load_registry()
    instance = registry.get_instance(instance_name)
    
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        sys.exit(1)
    
    # Run the service
    click.echo(f"Starting weather service for instance '{instance_name}'...")
    click.echo(f"Fetching weather data every {interval} seconds.")
    click.echo("Press Ctrl+C to stop.")
    
    run_weather_service(instance_name, interval, api_key, location)


if __name__ == "__main__":
    start_server()