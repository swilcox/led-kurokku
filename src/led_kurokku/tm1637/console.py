import logging

from .base_driver import BaseDriver


logger = logging.getLogger(__name__)


REVERSE_SEGMENTS = {
    0x3F: "0",  # 00111111
    0x06: "1",  # 00000110
    0x5B: "2",  # 01011011
    0x4F: "3",  # 01001111
    0x66: "4",  # 01100110
    0x6D: "5",  # 01101101
    0x7D: "6",  # 01111101
    0x07: "7",  # 00000111
    0x7F: "8",  # 01111111
    0x6F: "9",  # 01101111
    0x77: "A",  # 01110111
    0x7C: "B",  # 01111100
    0x39: "C",  # 00111001
    0x5E: "D",  # 01011110
    0x79: "E",  # 01111001
    0x71: "F",  # 01110001
    0x3D: "G",  # 00111101
    0x76: "H",  # 01110110
    0x30: "I",  # 00110000
    0x1E: "J",  # 00011110
    0x38: "L",  # 00111000
    0x55: "M",  # 01010101
    0x54: "N",  # 01010100
    0x5C: "O",  # 01011100
    0x73: "P",  # 01110011
    0x67: "Q",  # 01100111
    0x50: "R",  # 01010000
    0x78: "T",  # 01111000
    0x3E: "U",  # 00111110
    0x1C: "V",  # 00011100
    0x2A: "W",  # 00101010
    0x6E: "Y",  # 01101110
    0x40: "-",  # 01000000
    0x08: "_",  # 00001000
    0x63: "*",  # degree symbol
    0x00: " ",  # space
    0x58: "c",  # 01011000
}


class ConsoleDriver(BaseDriver):
    """
    Base class for TM1637 driver.
    """

    def __init__(self, brightness=2) -> None:
        """
        Initialize the TM1637 driver.
        """
        super().__init__(brightness=brightness)
        self._brightness = brightness
        self._driver_name = "console"

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display the given data on the TM1637 display.

        :param data: A list of integers to display.
        :param colon: boolean flag whether to display the colon.
        """
        # reverse lookup of the data for console text display
        data_str = "".join(REVERSE_SEGMENTS.get(d, "?") for d in data)
        logger.debug(f"Displaying data: {data_str} (colon: {colon})")
        logger.debug(f"Raw data: {data}")

    def clear(self) -> None:
        """
        Clear the display.
        """
        logger.debug("Clearing display")  # Placeholder for actual clear operation
