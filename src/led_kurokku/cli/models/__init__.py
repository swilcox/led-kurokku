"""Models for LED-Kurokku CLI."""

from .instance import KurokkuInstance, KurokkuRegistry, load_registry, save_registry
from .weather import WeatherLocation, LocationRegistry, load_location_registry, save_location_registry

__all__ = [
    "KurokkuInstance", 
    "KurokkuRegistry", 
    "load_registry", 
    "save_registry",
    "WeatherLocation",
    "LocationRegistry",
    "load_location_registry",
    "save_location_registry"
]
