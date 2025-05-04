import os
import time

from RPi import GPIO

from .base_driver import BaseDriver

# Allow GPIO pins to be configured via environment variables
CLK_PIN = int(os.environ.get("CLK_PIN", 23))  # GPIO23 by default
DIO_PIN = int(os.environ.get("DIO_PIN", 24))  # GPIO24 by default

# Disable GPIO warnings to prevent the "channel already in use" warnings
GPIO.setwarnings(False)

# TM1637 commands
ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
START_ADDR = 0xC0
BRIGHT_TYPICAL = 0x02


class LedDriver(BaseDriver):
    def __init__(self, clk_pin=CLK_PIN, dio_pin=DIO_PIN, brightness=BRIGHT_TYPICAL):
        super().__init__()
        self.clk_pin = clk_pin
        self.dio_pin = dio_pin
        self._brightness = brightness
        self._driver_name = "LED"
        
        # Ensure pins are cleaned up before setting them up again
        try:
            GPIO.cleanup([self.clk_pin, self.dio_pin])
        except:
            pass
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.OUT)
        GPIO.setup(self.dio_pin, GPIO.OUT)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        GPIO.output(self.dio_pin, GPIO.HIGH)

    def __del__(self):
        """Clean up GPIO on object destruction"""
        try:
            # Only clean up our specific pins to avoid conflicts with other GPIO users
            GPIO.cleanup([self.clk_pin, self.dio_pin])
        except:
            pass

    def _start(self):
        """Send start signal"""
        GPIO.output(self.dio_pin, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(self.clk_pin, GPIO.LOW)
        time.sleep(0.00001)

    def _stop(self):
        """Send stop signal"""
        GPIO.output(self.clk_pin, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(self.dio_pin, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.dio_pin, GPIO.HIGH)
        time.sleep(0.00001)

    def _write_byte(self, data):
        """Write a byte to TM1637"""
        for i in range(8):
            GPIO.output(self.clk_pin, GPIO.LOW)
            time.sleep(0.00001)

            # Set DIO pin based on the current bit
            if data & 0x01:
                GPIO.output(self.dio_pin, GPIO.HIGH)
            else:
                GPIO.output(self.dio_pin, GPIO.LOW)

            data >>= 1
            time.sleep(0.00001)
            GPIO.output(self.clk_pin, GPIO.HIGH)
            time.sleep(0.00001)

        # Wait for ACK
        GPIO.output(self.clk_pin, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(self.dio_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.clk_pin, GPIO.HIGH)
        time.sleep(0.00001)

        # Set DIO as input to read ACK
        GPIO.setup(self.dio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Wait for ACK from TM1637
        for _ in range(100):  # Timeout after 100 attempts
            if GPIO.input(self.dio_pin) == GPIO.LOW:
                break
            time.sleep(0.00001)

        # Set DIO back to output
        GPIO.setup(self.dio_pin, GPIO.OUT)
        time.sleep(0.00001)

    def clear(self):
        """Clear the display"""
        self.display([0, 0, 0, 0])

    def display(self, segments: list[int], colon=False):
        """Display the segments on the display
        segments is an array of 4 values (0-127) representing each digit"""
        # Command setting
        self._start()
        self._write_byte(ADDR_AUTO)
        self._stop()

        # Start address setting
        self._start()
        self._write_byte(START_ADDR)

        # Write each segment data
        for i, seg in enumerate(segments):
            # If colon is true, and we're at the 2nd position, turn on the colon
            if colon and i == 1:
                self._write_byte(seg | 0x80)  # Turn on colon
            else:
                self._write_byte(seg)

        self._stop()

        # Set brightness command
        self._start()
        self._write_byte(0x88 | self.brightness)
        self._stop()
