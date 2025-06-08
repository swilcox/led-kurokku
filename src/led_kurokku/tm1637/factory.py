from enum import StrEnum
import importlib.util

from .base_driver import BaseDriver


class DriverType(StrEnum):
    LED = "led"
    VIRTUAL = "virtual"
    CONSOLE = "console"
    WEBSOCKET = "websocket"


def create_driver(force_console=False, driver_type=None) -> BaseDriver:
    """
    Create a TM1637 driver instance.
    
    :param force_console: Force using the console driver regardless of available hardware.
    :param driver_type: Explicitly specify the driver type to use.
    :return: A BaseDriver instance.
    """
    if driver_type == DriverType.WEBSOCKET:
        from .websocket import WebSocketDriver
        return WebSocketDriver()
        
    if force_console:
        from .console import ConsoleDriver
        return ConsoleDriver()

    if driver_type == DriverType.CONSOLE:
        from .console import ConsoleDriver
        return ConsoleDriver()
        
    if driver_type == DriverType.VIRTUAL:
        from .virtual import VirtualDriver
        return VirtualDriver()
        
    # Auto-detect if no specific type is requested
    gpio_available = (
        importlib.util.find_spec("RPi") is not None
        and importlib.util.find_spec("RPi.GPIO") is not None
    )
    if gpio_available and (driver_type is None or driver_type == DriverType.LED):
        from .led import LedDriver
        return LedDriver()
        
    # Default to virtual if no hardware is available
    from .virtual import VirtualDriver
    return VirtualDriver()
