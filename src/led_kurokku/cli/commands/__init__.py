"""CLI commands for managing LED-Kurokku instances."""

from .instances import instances
from .config import config
from .template import template
from .alert import alert
from .weather import weather

__all__ = ["instances", "config", "template", "alert", "weather"]
