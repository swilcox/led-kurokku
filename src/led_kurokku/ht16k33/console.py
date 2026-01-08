"""Console driver for HT16K33 14-segment displays.

This driver logs display operations to the console for debugging purposes.
"""

import logging

from ..tm1637.base_driver import BaseDriver
from .segments import REVERSE_SEGMENTS_14

logger = logging.getLogger(__name__)


class HT16K33ConsoleDriver(BaseDriver):
    """
    Console logging driver for HT16K33 14-segment display.

    Logs display data to console instead of rendering to hardware.
    Useful for debugging and testing without physical display.
    """

    def __init__(self, brightness: int = 2) -> None:
        """
        Initialize the HT16K33 console driver.

        :param brightness: Initial brightness level (0-7).
        """
        super().__init__(brightness=brightness)
        self._driver_name = "HT16K33-console"

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Log display data to console.

        :param data: A list of 4 integers representing segment values.
        :param colon: Boolean flag for colon display.
        """
        if not isinstance(data, list) or len(data) != 4:
            logger.error(f"Invalid data: expected list of 4 integers, got {data}")
            return

        # Convert segment data to readable characters using reverse lookup
        data_str = "".join(REVERSE_SEGMENTS_14.get(d, "?") for d in data)

        logger.debug(f"HT16K33 Display: {data_str} (colon: {colon})")
        logger.debug(f"Raw 14-segment data: {[hex(d) for d in data]}")

    def clear(self) -> None:
        """Clear the display."""
        logger.debug("HT16K33 Clearing display")
