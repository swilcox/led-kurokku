"""
Weather location models for the LED-Kurokku CLI server.
"""

import datetime
import os
import json
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, field_validator


class WeatherLocation(BaseModel):
    """
    Weather location configuration.

    Attributes:
        name: Unique name/identifier for the location
        lat: Latitude coordinate
        lon: Longitude coordinate
        display_name: Human-readable name for display purposes
        is_default: Whether this is the default location for brightness control
    """

    name: Annotated[
        str, Field(min_length=1, description="Unique name for the location")
    ]
    lat: Annotated[float, Field(ge=-90, lt=90, description="Latitude coordinate")]
    lon: Annotated[float, Field(ge=-180, lt=180, description="Longitude coordinate")]
    display_name: str | None = None
    is_default: Annotated[
        bool, Field(default=False, description="Whether this is the default location for brightness control")
    ] = False

    @field_validator("name", mode="after")
    @classmethod
    def name_must_be_valid(cls, v):
        """Validate that the name is valid for use in Redis keys."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")

        # Ensure the name is lowercase, no spaces, suitable for Redis key
        processed = v.strip().lower().replace(" ", "_")
        if processed != v:
            raise ValueError(
                f"name must be lowercase with underscores instead of spaces, got '{v}', expected '{processed}'"
            )

        return v

    def __init__(self, **data):
        super().__init__(**data)
        # If display_name is None, set it based on name
        if self.display_name is None and self.name:
            self.display_name = self.name.replace("_", " ").title()

    model_config = {
        "validate_assignment": True,
    }


class WeatherConfig(BaseModel):
    """
    Weather service configuration.

    Attributes:
        locations: List of weather locations to monitor
        temperature_update_interval: Interval in seconds to update temperature data
        alerts_update_interval: Interval in seconds to update alert data
        openweather_api_key: API key for OpenWeather
    """

    locations: Annotated[
        list[WeatherLocation],
        Field(default_factory=list, description="List of weather locations to monitor"),
    ]
    temperature_update_interval: int = 300  # 5 minutes
    alerts_update_interval: int = 900  # 15 minutes
    openweather_api_key: str | None = None

    # Class variable for configuration path
    CONFIG_PATH: ClassVar[Path] = None
    
    @field_validator("locations")
    @classmethod
    def validate_default_location(cls, locations: list[WeatherLocation]) -> list[WeatherLocation]:
        """Validate that at most one location is marked as default."""
        default_locations = [loc for loc in locations if loc.is_default]
        
        if len(default_locations) > 1:
            names = [loc.name for loc in default_locations]
            raise ValueError(f"Only one location can be marked as default. Found multiple defaults: {', '.join(names)}")
            
        return locations

    @staticmethod
    def get_config_path() -> Path:
        """Return the path to the weather configuration file."""
        config_dir = Path(os.path.expanduser("~/.config/led-kurokku"))
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "weather_config.json"

    @classmethod
    def load(cls) -> "WeatherConfig":
        """Load the weather configuration from disk."""
        config_path = cls.get_config_path()

        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return cls.model_validate(data)
        except Exception as e:
            print(f"Error loading weather configuration: {e}")
            return cls()

    def save(self) -> None:
        """Save the weather configuration to disk."""
        config_path = self.get_config_path()

        with open(config_path, "w") as f:
            f.write(self.model_dump_json(indent=2))


# Location registry functions
def get_location_registry_path() -> Path:
    """Return the path to the registry file."""
    config_dir = Path(os.path.expanduser("~/.config/led-kurokku"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "weather_locations.json"


class LocationRegistry(BaseModel):
    """Registry of all weather locations."""

    locations: Annotated[
        list[WeatherLocation],
        Field(description="List of weather locations", default_factory=list),
    ]

    def add_location(self, location: WeatherLocation) -> None:
        """Add a location to the registry."""
        # Check if a location with the same name already exists
        if any(l.name == location.name for l in self.locations):
            raise ValueError(f"Location with name '{location.name}' already exists")

        self.locations.append(location)

    def remove_location(self, name: str) -> WeatherLocation | None:
        """Remove a location from the registry."""
        for i, location in enumerate(self.locations):
            if location.name == name:
                return self.locations.pop(i)
        return None

    def get_location(self, name: str) -> WeatherLocation | None:
        """Get a location by name."""
        for location in self.locations:
            if location.name == name:
                return location
        return None

    def update_location(self, name: str, new_location: WeatherLocation) -> bool:
        """Update an existing location."""
        for i, location in enumerate(self.locations):
            if location.name == name:
                self.locations[i] = new_location
                return True
        return False


def load_location_registry() -> LocationRegistry:
    """Load the registry from disk."""
    registry_path = get_location_registry_path()

    if not registry_path.exists():
        return LocationRegistry()

    try:
        with open(registry_path, "r") as f:
            data = json.load(f)
        return LocationRegistry.model_validate(data)
    except Exception as e:
        # If there's an error loading the registry, return an empty one
        print(f"Error loading location registry: {e}")
        return LocationRegistry()


def save_location_registry(registry: LocationRegistry) -> None:
    """Save the registry to disk."""
    registry_path = get_location_registry_path()

    with open(registry_path, "w") as f:
        f.write(registry.model_dump_json())