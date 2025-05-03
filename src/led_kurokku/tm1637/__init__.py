import time

from .base_driver import BaseDriver


class TM1637:
    """
    Base class for TM1637 display modules.
    This class provides the basic structure and constants used by derived classes.
    """

    display_length = 4  # Number of digits on the display
    colon_position = 2  # Position of the colon in the display segments (0-indexed)

    # Segments for displaying digits and characters
    SEGMENTS = {
        "0": 0x3F,
        "1": 0x06,
        "2": 0x5B,
        "3": 0x4F,
        "4": 0x66,
        "5": 0x6D,
        "6": 0x7D,
        "7": 0x07,
        "8": 0x7F,
        "9": 0x6F,
        "A": 0x77,
        "b": 0x7C,
        "c": 0x58,
        "C": 0x39,
        "d": 0x5E,
        "E": 0x79,
        "F": 0x71,
        "G": 0x3D,
        "H": 0x76,
        "h": 0x74,
        "I": 0x30,
        "J": 0x1E,
        "k": 0x76,
        "L": 0x38,
        "m": 0x55,
        "n": 0x54,
        "o": 0x5C,
        "O": 0x3F,
        "P": 0x73,
        "q": 0x67,
        "r": 0x50,
        "S": 0x6D,
        "t": 0x78,
        "U": 0x3E,
        "v": 0x1C,
        "w": 0x2A,
        "x": 0x76,
        "y": 0x6E,
        "z": 0x5B,
        "-": 0x40,
        "_": 0x08,
        "*": 0x63,  # degree symbol
        " ": 0x00,
    }

    def __init__(self, driver=BaseDriver):
        self.driver = driver

    def clear(self):
        """Clear the display"""
        self.driver.clear()

    @property
    def brightness(self):
        return self.driver.brightness

    @brightness.setter
    def brightness(self, value):
        self.driver.brightness = value

    def display(self, segments: list[int], colon=False):
        """Display the segments on the display"""
        self.driver.display(segments, colon)

    def show_number(self, number: int | float):
        """Display a number (integer/float) on the display"""
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
                segments[pos - 1] |= 0x80
            elif char in self.SEGMENTS:
                if pos < 4:
                    segments[pos] = self.SEGMENTS[char]
                    pos += 1

        # Right-align the number
        if pos < 4:
            segments = [0] * (4 - pos) + segments[:pos]

        self.display(segments)

    def show_text(self, text: str):
        """Display a text on the display (limited to 4 characters)"""
        text = text[:4]  # Limit to 4 chars and convert to uppercase
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

    def show_time(self, hour: int, minute: int, colon=True):
        """Display time in HH:MM format with optional colon"""
        segments = [0] * 4

        # Hours
        segments[0] = self.SEGMENTS[str(hour // 10)]
        segments[1] = self.SEGMENTS[str(hour % 10)]

        # Minutes
        segments[2] = self.SEGMENTS[str(minute // 10)]
        segments[3] = self.SEGMENTS[str(minute % 10)]

        self.display(segments, colon)
