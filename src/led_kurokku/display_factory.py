"""Unified display factory for creating TM1637 or HT16K33 displays.

Provides runtime selection between different display hardware types.
"""

import logging
from enum import StrEnum
from typing import Union

from .ht16k33 import HT16K33
from .ht16k33.factory import create_driver as create_ht16k33_driver
from .tm1637 import TM1637
from .tm1637.base_driver import BaseDriver
from .tm1637.factory import DriverType, create_driver as create_tm1637_driver

logger = logging.getLogger(__name__)


class DisplayType(StrEnum):
    """Display hardware types supported by LED-Kurokku."""

    TM1637 = "tm1637"
    HT16K33 = "ht16k33"


def create_display(
    display_type: DisplayType | str = DisplayType.TM1637,
    driver_type: DriverType | None = None,
    force_console: bool = False,
    driver_instance: BaseDriver | None = None,
) -> Union[TM1637, HT16K33]:
    """
    Create a display instance (TM1637 or HT16K33) with the appropriate driver.

    This factory enables runtime selection between different display hardware types
    while maintaining a consistent API for widgets.

    :param display_type: Type of display hardware ("tm1637" or "ht16k33").
    :param driver_type: Specific driver to use (led, virtual, console, websocket).
    :param force_console: Force console driver (for debugging).
    :param driver_instance: Existing driver instance to use (overrides other options).
    :return: TM1637 or HT16K33 instance with configured driver.
    """
    # Convert string to DisplayType if needed
    if isinstance(display_type, str):
        display_type = DisplayType(display_type)

    logger.info(f"Creating display: {display_type}, driver: {driver_type}")

    if display_type == DisplayType.HT16K33:
        # Create HT16K33 14-segment display
        if driver_instance:
            driver = driver_instance
        else:
            driver = create_ht16k33_driver(force_console=force_console, driver_type=driver_type)
        return HT16K33(driver=driver)

    else:
        # Default to TM1637 7-segment display
        if driver_instance:
            driver = driver_instance
        else:
            driver = create_tm1637_driver(force_console=force_console, driver_type=driver_type)
        return TM1637(driver=driver)
