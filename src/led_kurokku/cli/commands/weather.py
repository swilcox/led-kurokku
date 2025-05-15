"""
CLI commands for managing weather locations and starting the weather service.
"""

import click
import json
import os
import sys
from typing import Optional

from ..models.weather import WeatherConfig, WeatherLocation
from ..services.weather_service import run_weather_service


@click.group()
def weather():
    """Manage weather locations and service."""
    pass


@weather.command("locations")
def list_locations():
    """List all configured weather locations."""
    config = WeatherConfig.load()
    
    if not config.locations:
        click.echo("No weather locations configured.")
        return
    
    click.echo("Configured weather locations:")
    for location in config.locations:
        click.echo(f"  - {location.display_name}")
        click.echo(f"    Name: {location.name}")
        click.echo(f"    Coordinates: {location.lat}, {location.lon}")
        click.echo("")


@weather.command("add-location")
@click.argument("name")
@click.argument("lat", type=float)
@click.argument("lon", type=float)
@click.option("--display-name", "-d", help="Display name for the location")
def add_location(name: str, lat: float, lon: float, display_name: Optional[str]):
    """Add a new weather location."""
    config = WeatherConfig.load()
    
    # Check if location with this name already exists
    if any(l.name == name for l in config.locations):
        click.echo(f"Location with name '{name}' already exists.")
        return
    
    # Create the new location
    try:
        location = WeatherLocation(
            name=name,
            lat=lat,
            lon=lon,
            display_name=display_name,
        )
    except ValueError as e:
        click.echo(f"Error creating location: {e}")
        return
    
    # Add the location to the configuration
    config.locations.append(location)
    config.save()
    
    click.echo(f"Added location '{location.display_name}'.")


@weather.command("remove-location")
@click.argument("name")
def remove_location(name: str):
    """Remove a weather location."""
    config = WeatherConfig.load()
    
    # Find the location
    for i, location in enumerate(config.locations):
        if location.name == name:
            config.locations.pop(i)
            config.save()
            click.echo(f"Removed location '{name}'.")
            return
    
    click.echo(f"No location found with name '{name}'.")


@weather.command("set-api-key")
@click.argument("api_key")
def set_api_key(api_key: str):
    """Set the OpenWeather API key."""
    config = WeatherConfig.load()
    config.openweather_api_key = api_key
    config.save()
    click.echo("API key set successfully.")


@weather.command("set-intervals")
@click.option("--temperature", "-t", type=int, help="Temperature update interval in seconds")
@click.option("--alerts", "-a", type=int, help="Alerts update interval in seconds")
def set_intervals(temperature: Optional[int], alerts: Optional[int]):
    """Set the update intervals for weather data."""
    config = WeatherConfig.load()
    
    if temperature is not None:
        if temperature < 60:
            click.echo("Temperature update interval must be at least 60 seconds.")
            return
        config.temperature_update_interval = temperature
    
    if alerts is not None:
        if alerts < 60:
            click.echo("Alerts update interval must be at least 60 seconds.")
            return
        config.alerts_update_interval = alerts
    
    config.save()
    click.echo("Update intervals set successfully.")
    click.echo(f"Temperature update interval: {config.temperature_update_interval} seconds")
    click.echo(f"Alerts update interval: {config.alerts_update_interval} seconds")


@weather.command("show-config")
def show_config():
    """Show the current weather configuration."""
    config = WeatherConfig.load()
    
    # Mask the API key for security
    config_dict = json.loads(config.model_dump_json())
    if config_dict.get("openweather_api_key"):
        api_key = config_dict["openweather_api_key"]
        masked_key = f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}" if len(api_key) > 8 else "********"
        config_dict["openweather_api_key"] = masked_key
    
    click.echo(json.dumps(config_dict, indent=2))


@weather.command("start")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def start_weather_service(debug: bool):
    """Start the weather service."""
    import logging
    
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Load configuration
    config = WeatherConfig.load()
    
    # Validate configuration
    if not config.locations:
        click.echo("No weather locations configured. Use 'kurokku-cli weather add-location' to add one.")
        return
    
    if not config.openweather_api_key:
        click.echo("No OpenWeather API key configured. Use 'kurokku-cli weather set-api-key' to set one.")
        return
    
    # Run the service
    click.echo("Starting weather service...")
    click.echo(f"Monitoring {len(config.locations)} locations")
    click.echo(f"Temperature updates every {config.temperature_update_interval} seconds")
    click.echo(f"Alert updates every {config.alerts_update_interval} seconds")
    click.echo("Press Ctrl+C to stop.")
    
    try:
        run_weather_service(config)
    except KeyboardInterrupt:
        click.echo("\nWeather service stopped by user.")
    except Exception as e:
        click.echo(f"Error running weather service: {e}")
        sys.exit(1)