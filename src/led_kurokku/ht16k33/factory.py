"""Factory for creating HT16K33 drivers.

Provides intelligent driver selection based on available hardware and configuration.
"""

import importlib.util
from enum import StrEnum

from ..tm1637.base_driver import BaseDriver


class DriverType(StrEnum):
    """Driver types available for HT16K33 displays."""

    LED = "led"
    VIRTUAL = "virtual"
    CONSOLE = "console"
    WEBSOCKET = "websocket"


def create_driver(force_console: bool = False, driver_type: DriverType | None = None) -> BaseDriver:
    """
    Create an HT16K33 driver instance.

    Selection logic:
    1. If driver_type=WEBSOCKET is explicitly requested, use WebSocket driver
    2. If force_console=True or driver_type=CONSOLE, use Console driver
    3. If driver_type=VIRTUAL, use Virtual driver
    4. If smbus2 is available and driver_type is None or LED, use LED hardware driver
    5. Default fallback: Virtual driver

    :param force_console: Force using the console driver regardless of available hardware.
    :param driver_type: Explicitly specify the driver type to use.
    :return: A BaseDriver instance for HT16K33.
    """
    if driver_type == DriverType.WEBSOCKET:
        from .websocket import HT16K33WebSocketDriver

        return HT16K33WebSocketDriver()

    if force_console:
        from .console import HT16K33ConsoleDriver

        return HT16K33ConsoleDriver()

    if driver_type == DriverType.CONSOLE:
        from .console import HT16K33ConsoleDriver

        return HT16K33ConsoleDriver()

    if driver_type == DriverType.VIRTUAL:
        from .virtual import HT16K33VirtualDriver

        return HT16K33VirtualDriver()

    # Auto-detect: Check if smbus2 is available for I2C hardware driver
    smbus2_available = importlib.util.find_spec("smbus2") is not None

    if smbus2_available and (driver_type is None or driver_type == DriverType.LED):
        from .led import HT16K33LedDriver

        return HT16K33LedDriver()

    # Default fallback: Virtual terminal driver
    from .virtual import HT16K33VirtualDriver

    return HT16K33VirtualDriver()
