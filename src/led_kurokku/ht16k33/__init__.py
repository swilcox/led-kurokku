"""HT16K33 14-segment display module.

Provides high-level interface for HT16K33 14-segment LED displays.
API is compatible with TM1637 module for seamless widget integration.
"""

from ..tm1637.base_driver import BaseDriver
from .segments import SEGMENTS_14


class HT16K33:
    """
    Wrapper class for HT16K33 14-segment display modules.

    Provides high-level interface compatible with TM1637 for existing widgets.
    Uses 14-segment character mapping for full alphanumeric support.
    """

    display_length = 4  # Number of digits on the display
    colon_position = 2  # Position of the colon in the display segments (0-indexed)

    # 14-segment character mapping
    SEGMENTS = SEGMENTS_14

    def __init__(self, driver: BaseDriver):
        """
        Initialize the HT16K33 display.

        :param driver: Driver instance (hardware, virtual, console, or websocket).
        """
        self.driver = driver

    def clear(self):
        """Clear the display."""
        self.driver.clear()

    @property
    def brightness(self):
        """Get the current brightness level (0-7)."""
        return self.driver.brightness

    @brightness.setter
    def brightness(self, value):
        """Set the brightness level (0-7)."""
        self.driver.brightness = value

    def display(self, segments: list[int], colon=False):
        """
        Display the segments on the display.

        :param segments: List of 4 integers representing 14-segment values.
        :param colon: Boolean flag for colon display.
        """
        self.driver.display(segments, colon)

    def show_number(self, number: int | float):
        """
        Display a number (integer or float) on the display.

        :param number: The number to display.
        """
        if isinstance(number, float):
            # For float, show with 1 decimal place
            number_str = f"{number:.1f}"
        else:
            number_str = str(int(number))

        # Limit to 4 digits
        if len(number_str) > 4:
            if "." in number_str and number_str.index(".") <= 3:
                # Keep decimal point if within first 3 characters
                number_str = number_str[:5]  # Keep decimal point and one decimal digit
            else:
                number_str = number_str[:4]  # Just first 4 digits

        segments = [0] * 4
        pos = 0

        for char in number_str:
            if char == "." and pos > 0:
                # Add decimal point to previous digit
                # For 14-segment displays, decimal point is typically bit 15
                segments[pos - 1] |= 0x8000
            elif char in self.SEGMENTS:
                if pos < 4:
                    segments[pos] = self.SEGMENTS[char]
                    pos += 1

        # Right-align the number
        if pos < 4:
            segments = [0] * (4 - pos) + segments[:pos]

        self.display(segments)

    def show_text(self, text: str):
        """
        Display text on the display (limited to 4 characters).

        :param text: The text to display.
        """
        text = text[:4]  # Limit to 4 chars
        segments = [0] * 4

        for i, char in enumerate(text):
            if i >= 4:
                break
            if char in self.SEGMENTS:
                segments[i] = self.SEGMENTS[char]
            elif char.lower() in self.SEGMENTS:
                segments[i] = self.SEGMENTS[char.lower()]
            elif char.upper() in self.SEGMENTS:
                segments[i] = self.SEGMENTS[char.upper()]

        self.display(segments)

    def show_time(self, hour: int, minute: int, colon=True, leading_blank=False):
        """
        Display time in HH:MM format with optional colon.

        :param hour: Hour value (0-23 or 0-12).
        :param minute: Minute value (0-59).
        :param colon: Boolean flag to show colon.
        :param leading_blank: Boolean flag to blank leading zero for single-digit hours.
        """
        segments = [0] * 4

        # Hours
        if leading_blank and hour < 10:
            segments[0] = self.SEGMENTS[" "]  # Blank for single digit hours
        else:
            segments[0] = self.SEGMENTS[str(hour // 10)]
        segments[1] = self.SEGMENTS[str(hour % 10)]

        # Minutes
        segments[2] = self.SEGMENTS[str(minute // 10)]
        segments[3] = self.SEGMENTS[str(minute % 10)]

        self.display(segments, colon)
