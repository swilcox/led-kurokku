from enum import StrEnum
import importlib.util

from .base_driver import BaseDriver

class DriverType(StrEnum):
    LED = "led"
    VIRTUAL = "virtual"
    CONSOLE = "console"

def create_driver(force_console=False) -> BaseDriver:
    if force_console:
        from .console import ConsoleDriver
        return ConsoleDriver()

    gpio_available = (importlib.util.find_spec("RPi") is not None and importlib.util.find_spec("RPi.GPIO") is not None)
    if gpio_available:
        from .led import LedDriver
        return LedDriver()
    from .virtual import VirtualDriver
    return VirtualDriver()
