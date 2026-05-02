"""Hardware I2C driver for HT16K33 14-segment displays.

Implements I2C communication with HT16K33 chip using smbus2 library.
"""

import logging
import os

from smbus2 import SMBus

from ..tm1637.base_driver import BaseDriver

logger = logging.getLogger(__name__)

# HT16K33 I2C configuration (configurable via environment variables)
HT16K33_ADDRESS = int(os.environ.get("HT16K33_ADDRESS", "0x70"), 16)
HT16K33_BUS = int(os.environ.get("HT16K33_BUS", "1"))

# HT16K33 commands
HT16K33_SYSTEM_SETUP = 0x20  # System setup register
HT16K33_OSCILLATOR_ON = 0x01  # Turn on oscillator
HT16K33_DISPLAY_SETUP = 0x80  # Display setup register
HT16K33_DISPLAY_ON = 0x01  # Turn on display
HT16K33_BRIGHTNESS_CMD = 0xE0  # Brightness command (0xE0-0xEF)


class HT16K33LedDriver(BaseDriver):
    """
    Hardware driver for HT16K33 14-segment display via I2C.

    Uses smbus2 library for I2C communication with HT16K33 chip.
    Supports 4-digit 14-segment displays with brightness control (0-7 external, 0-15 internal).
    """

    def __init__(self, address: int = HT16K33_ADDRESS, bus: int = HT16K33_BUS, brightness: int = 2):
        """
        Initialize the HT16K33 hardware driver.

        :param address: I2C address of HT16K33 (default 0x70).
        :param bus: I2C bus number (default 1 for Raspberry Pi).
        :param brightness: Initial brightness level (0-7).
        """
        super().__init__(brightness=brightness)
        self.address = address
        self.bus_number = bus
        self._driver_name = "HT16K33-LED"

        # Buffer to track current display state (reduces I2C writes and flicker)
        # Initialize with 0xFF to ensure first clear() actually writes to hardware
        # (otherwise comparison shows "no change" and garbage in display RAM persists)
        self._display_buffer = [0xFF] * 16

        # Initialize I2C bus
        try:
            self.bus = SMBus(self.bus_number)
            self._initialize_display()
            logger.info(f"HT16K33 initialized on I2C bus {bus} at address 0x{address:02X}")
        except Exception as e:
            logger.error(f"Failed to initialize HT16K33: {e}")
            raise

    def _initialize_display(self) -> None:
        """Initialize the HT16K33 display chip."""
        # Turn on system oscillator
        self.bus.write_byte(self.address, HT16K33_SYSTEM_SETUP | HT16K33_OSCILLATOR_ON)

        # Turn on display (no blinking)
        self.bus.write_byte(self.address, HT16K33_DISPLAY_SETUP | HT16K33_DISPLAY_ON)

        # Set initial brightness
        self._set_brightness_hardware(self.brightness)

        # Clear display
        self.clear()

    def _set_brightness_hardware(self, level: int) -> None:
        """
        Set brightness on the hardware.

        Maps 0-7 range to HT16K33's 0-15 range for compatibility.
        Uses linear mapping: 0→0, 1→2, 2→4, 3→6, 4→8, 5→10, 6→12, 7→14

        :param level: Brightness level (0-7).
        """
        # Map 0-7 to 0-14 (multiply by 2, capped at 15)
        hw_brightness = min(level * 2, 15) if level > 0 else 0
        self.bus.write_byte(self.address, HT16K33_BRIGHTNESS_CMD | hw_brightness)
        logger.debug(f"Set brightness: {level} (hardware: {hw_brightness}/15)")

    @BaseDriver.brightness.setter
    def brightness(self, value: int) -> None:
        """
        Set brightness level and update hardware.

        :param value: Brightness level (0-7).
        """
        if 0 <= value <= 7:
            self._brightness = value
            self._set_brightness_hardware(value)
        else:
            raise ValueError("Brightness must be between 0 and 7")

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display the segments on the HT16K33.

        HT16K33 display RAM layout (configurable via environment variable):
        - Each digit uses 2 bytes (16 bits for 14-segment + extras)
        - Sequential layout: 0x00-0x01 (digit 0), 0x02-0x03 (digit 1),
                           0x04-0x05 (digit 2), 0x06-0x07 (digit 3)

        :param data: List of 4 integers (16-bit segment values for 14-segment display).
        :param colon: Boolean flag for colon display.
        """
        if not isinstance(data, list) or len(data) != 4:
            raise ValueError("Data must be a list of 4 integers")

        # Create new buffer based on current state (avoid unnecessary zeros)
        buffer = self._display_buffer.copy()

        # Check for Adafruit-style layout (with colon gap) via environment variable
        # Default to sequential layout (most common for generic boards)
        use_adafruit_layout = os.environ.get("HT16K33_ADAFRUIT_LAYOUT", "").lower() == "true"

        # Map 4 digits to HT16K33 positions
        for i, segment_data in enumerate(data):
            if use_adafruit_layout:
                # Adafruit layout: digit 0-1 at 0x00-0x03, colon at 0x04-0x05, digit 2-3 at 0x06-0x09
                if i < 2:
                    pos = i * 2
                else:
                    pos = (i * 2) + 2  # Skip colon position
            else:
                # Sequential layout: digits at 0x00, 0x02, 0x04, 0x06
                pos = i * 2

            # For colon display on digit 1 (second digit) in sequential layout
            # Add colon bits to the segment data if colon is enabled
            if colon and i == 1 and not use_adafruit_layout:
                # On many boards, colon/decimal is controlled by high bits of digit 1
                # Try bit 14 for decimal point
                segment_data = segment_data | 0x4000

            # Split 16-bit segment data into 2 bytes (little-endian)
            buffer[pos] = segment_data & 0xFF
            buffer[pos + 1] = (segment_data >> 8) & 0xFF

        # Handle colon for Adafruit layout (separate position)
        if use_adafruit_layout:
            buffer[4] = 0xFF if colon else 0x00
            buffer[5] = 0x00

        # Only write to I2C if buffer changed (reduces flicker)
        if buffer != self._display_buffer:
            try:
                # Find contiguous changed regions to minimize I2C writes
                # This significantly reduces flicker by only writing changed bytes
                i = 0
                while i < len(buffer):
                    # Skip unchanged bytes
                    while i < len(buffer) and buffer[i] == self._display_buffer[i]:
                        i += 1

                    if i >= len(buffer):
                        break

                    # Find end of changed region
                    start = i
                    while i < len(buffer) and buffer[i] != self._display_buffer[i]:
                        i += 1

                    # Write only the changed bytes
                    changed_bytes = buffer[start:i]
                    self.bus.write_i2c_block_data(self.address, start, changed_bytes)
                    logger.debug(f"Updated bytes {start}-{i-1}: {[hex(b) for b in changed_bytes]}")

                self._display_buffer = buffer.copy()
                logger.debug(f"Display updated: digits={[hex(d) for d in data]}, colon={colon}")
            except Exception as e:
                logger.error(f"Failed to write to HT16K33: {e}")
                raise

    def clear(self) -> None:
        """Clear the display by setting all segments to off."""
        self.display([0, 0, 0, 0], colon=False)

    def __del__(self):
        """Clean up I2C bus on object destruction."""
        try:
            if hasattr(self, "bus"):
                self.bus.close()
                logger.debug("I2C bus closed")
        except Exception as e:
            logger.error(f"Error closing I2C bus: {e}")
