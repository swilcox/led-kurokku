"""
Weather location models for the LED-Kurokku CLI server.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class WeatherLocation(BaseModel):
    """
    Weather location configuration.
    
    Attributes:
        name: Unique name/identifier for the location
        lat: Latitude coordinate
        lon: Longitude coordinate
        display_name: Human-readable name for display purposes
    """
    
    name: str
    lat: float
    lon: float
    display_name: Optional[str] = None
    
    @validator("name")
    def name_must_be_valid(cls, v):
        """Validate that the name is valid for use in Redis keys."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        
        # Ensure the name is lowercase, no spaces, suitable for Redis key
        processed = v.strip().lower().replace(" ", "_")
        if processed != v:
            raise ValueError(f"name must be lowercase with underscores instead of spaces, got '{v}', expected '{processed}'")
        
        return v
    
    @validator("lat")
    def lat_must_be_valid(cls, v):
        """Validate latitude is between -90 and 90."""
        if v < -90 or v > 90:
            raise ValueError("latitude must be between -90 and 90")
        return v
    
    @validator("lon")
    def lon_must_be_valid(cls, v):
        """Validate longitude is between -180 and 180."""
        if v < -180 or v > 180:
            raise ValueError("longitude must be between -180 and 180")
        return v
    
    @validator("display_name", always=True)
    def set_display_name(cls, v, values):
        """Set display_name to name if not provided."""
        if v is None and "name" in values:
            return values["name"].replace("_", " ").title()
        return v


class WeatherConfig(BaseModel):
    """
    Weather service configuration.
    
    Attributes:
        locations: List of weather locations to monitor
        temperature_update_interval: Interval in seconds to update temperature data
        alerts_update_interval: Interval in seconds to update alert data
        openweather_api_key: API key for OpenWeather
    """
    
    locations: List[WeatherLocation] = []
    temperature_update_interval: int = 300  # 5 minutes
    alerts_update_interval: int = 900  # 15 minutes
    openweather_api_key: Optional[str] = None


def get_weather_config_path() -> Path:
    """Return the path to the weather configuration file."""
    config_dir = Path(os.path.expanduser("~/.config/led-kurokku"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "weather_config.json"


def load_weather_config() -> WeatherConfig:
    """Load the weather configuration from disk."""
    config_path = get_weather_config_path()
    
    if not config_path.exists():
        return WeatherConfig()
    
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        return WeatherConfig.model_validate(data)
    except Exception as e:
        print(f"Error loading weather configuration: {e}")
        return WeatherConfig()


def save_weather_config(config: WeatherConfig) -> None:
    """Save the weather configuration to disk."""
    config_path = get_weather_config_path()
    
    with open(config_path, "w") as f:
        f.write(config.model_dump_json(indent=2))