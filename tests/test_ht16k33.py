"""Unit tests for HT16K33 14-segment display module."""

import pytest

from led_kurokku.display_factory import DisplayType, create_display
from led_kurokku.ht16k33 import HT16K33
from led_kurokku.ht16k33.console import HT16K33ConsoleDriver
from led_kurokku.ht16k33.factory import DriverType, create_driver
from led_kurokku.ht16k33.segments import REVERSE_SEGMENTS_14, SEGMENTS_14
from led_kurokku.ht16k33.virtual import HT16K33VirtualDriver
from led_kurokku.tm1637 import TM1637


def test_ht16k33_segments_has_required_characters():
    """Test that 14-segment character map has all required characters."""
    # Numbers
    for char in "0123456789":
        assert char in SEGMENTS_14, f"Missing number: {char}"

    # Uppercase letters
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert char in SEGMENTS_14, f"Missing uppercase letter: {char}"

    # Essential special characters
    for char in " -_*":
        assert char in SEGMENTS_14, f"Missing special character: {char}"


def test_ht16k33_reverse_segments_mapping():
    """Test reverse segment mapping for debugging."""
    # Test that reverse mapping dict exists and is populated
    assert len(REVERSE_SEGMENTS_14) > 0
    # Test that space character maps correctly (unique value)
    assert REVERSE_SEGMENTS_14[SEGMENTS_14[" "]] == " "
    # Test that some character values are in the reverse mapping
    for char in "123456789":  # Skip 0 and O which may collide
        assert SEGMENTS_14[char] in REVERSE_SEGMENTS_14


def test_ht16k33_console_driver_initialization():
    """Test console driver initialization."""
    driver = HT16K33ConsoleDriver(brightness=5)
    assert driver.brightness == 5
    assert driver.name == "HT16K33-console"


def test_ht16k33_console_driver_display():
    """Test console driver display method."""
    driver = HT16K33ConsoleDriver()

    # Should not raise
    driver.display([0x00F7, 0x128F, 0x0039, 0x120F], colon=True)
    driver.clear()


def test_ht16k33_console_driver_brightness():
    """Test console driver brightness property."""
    driver = HT16K33ConsoleDriver()

    # Test setting brightness
    driver.brightness = 7
    assert driver.brightness == 7

    # Test invalid brightness
    with pytest.raises(ValueError):
        driver.brightness = 8

    with pytest.raises(ValueError):
        driver.brightness = -1


def test_ht16k33_virtual_driver_initialization():
    """Test virtual driver initialization."""
    driver = HT16K33VirtualDriver()
    assert driver.brightness == 2  # default
    assert driver.name == "HT16K33-virtual"
    assert driver.display_height == 7  # 14-segment needs more height


def test_ht16k33_virtual_driver_display():
    """Test virtual driver display method."""
    driver = HT16K33VirtualDriver()

    # Should not raise
    driver.display([SEGMENTS_14["1"], SEGMENTS_14["2"], SEGMENTS_14["3"], SEGMENTS_14["4"]], colon=True)
    driver.clear()


def test_ht16k33_wrapper_initialization():
    """Test HT16K33 wrapper class initialization."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    assert ht.display_length == 4
    assert ht.colon_position == 2
    assert ht.SEGMENTS == SEGMENTS_14


def test_ht16k33_wrapper_brightness():
    """Test HT16K33 wrapper brightness property."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    # Test brightness property
    ht.brightness = 7
    assert ht.brightness == 7
    assert driver.brightness == 7


def test_ht16k33_wrapper_show_time():
    """Test HT16K33 show_time method."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    # Should not raise
    ht.show_time(12, 34, colon=True)
    ht.show_time(0, 0, colon=False)
    ht.show_time(9, 30, colon=True, leading_blank=True)


def test_ht16k33_wrapper_show_number():
    """Test HT16K33 show_number method."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    # Test integer
    ht.show_number(42)

    # Test float
    ht.show_number(98.6)

    # Test large number (truncation)
    ht.show_number(123456)

    # Test negative number
    ht.show_number(-123)


def test_ht16k33_wrapper_show_text():
    """Test HT16K33 show_text method."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    # Test text display
    ht.show_text("ABCD")
    ht.show_text("test")
    ht.show_text("Hi")  # Less than 4 chars
    ht.show_text("TOOLONG")  # More than 4 chars, should truncate


def test_ht16k33_wrapper_clear():
    """Test HT16K33 clear method."""
    driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=driver)

    # Should not raise
    ht.clear()


def test_ht16k33_factory_console_driver():
    """Test factory creates console driver."""
    driver = create_driver(driver_type=DriverType.CONSOLE)
    assert isinstance(driver, HT16K33ConsoleDriver)


def test_ht16k33_factory_virtual_driver():
    """Test factory creates virtual driver."""
    driver = create_driver(driver_type=DriverType.VIRTUAL)
    assert isinstance(driver, HT16K33VirtualDriver)


def test_ht16k33_factory_force_console():
    """Test factory force_console parameter."""
    driver = create_driver(force_console=True)
    assert isinstance(driver, HT16K33ConsoleDriver)


def test_display_factory_creates_ht16k33():
    """Test unified display factory creates HT16K33."""
    display = create_display(display_type=DisplayType.HT16K33, driver_type=DriverType.CONSOLE)

    assert isinstance(display, HT16K33)
    assert display.display_length == 4


def test_display_factory_creates_tm1637():
    """Test unified display factory creates TM1637."""
    display = create_display(display_type=DisplayType.TM1637, driver_type=DriverType.CONSOLE)

    assert isinstance(display, TM1637)
    assert display.display_length == 4


def test_display_factory_default_is_tm1637():
    """Test unified display factory defaults to TM1637."""
    display = create_display(driver_type=DriverType.CONSOLE)

    assert isinstance(display, TM1637)


def test_display_compatibility_interface():
    """Test that both TM1637 and HT16K33 have compatible interfaces."""
    tm = create_display(DisplayType.TM1637, DriverType.CONSOLE)
    ht = create_display(DisplayType.HT16K33, DriverType.CONSOLE)

    # Both should have these methods
    for display in [tm, ht]:
        assert hasattr(display, "show_time")
        assert hasattr(display, "show_text")
        assert hasattr(display, "show_number")
        assert hasattr(display, "clear")
        assert hasattr(display, "display")
        assert hasattr(display, "brightness")
        assert hasattr(display, "display_length")
        assert hasattr(display, "SEGMENTS")


def test_ht16k33_14segment_vs_tm1637_7segment():
    """Test that HT16K33 has more characters than TM1637."""
    from led_kurokku.tm1637 import TM1637
    from led_kurokku.tm1637.console import ConsoleDriver

    tm_driver = ConsoleDriver()
    tm = TM1637(driver=tm_driver)

    ht_driver = HT16K33ConsoleDriver()
    ht = HT16K33(driver=ht_driver)

    # HT16K33 should have more characters available
    assert len(ht.SEGMENTS) >= len(tm.SEGMENTS)

    # Both should have basic numbers
    for char in "0123456789":
        assert char in tm.SEGMENTS
        assert char in ht.SEGMENTS

    # HT16K33 should have full uppercase alphabet that TM1637 might not
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert char in ht.SEGMENTS
