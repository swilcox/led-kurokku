import asyncio

import pytest

from led_kurokku.tm1637 import TM1637
from led_kurokku.tm1637.console import ConsoleDriver

from led_kurokku.widgets.clock import (
    _convert_to_12_hour_format,
    ClockWidget,
    ClockWidgetConfig,
)


def test_convert_to_12_hour_format():
    assert _convert_to_12_hour_format(12) == 12
    assert _convert_to_12_hour_format(13) == 1
    assert _convert_to_12_hour_format(0) == 12
    assert _convert_to_12_hour_format(23) == 11


def test_tm1637_show_time_leading_blank():
    tm = TM1637(driver=ConsoleDriver())
    
    # Test 12-hour mode with leading blank for single digit hours
    tm.show_time(9, 30, colon=True, leading_blank=True)
    # Should display " 9:30" (blank space for tens digit)
    
    # Test 24-hour mode without leading blank
    tm.show_time(9, 30, colon=True, leading_blank=False)
    # Should display "09:30" (zero for tens digit)


@pytest.mark.asyncio
async def test_clock_widget(fake_async_redis):
    config = ClockWidgetConfig(
        use_24_hour_format=True,
        duration=1,
    )
    tm = TM1637(driver=ConsoleDriver())
    faux_stop_event = asyncio.Event()
    widget = ClockWidget(
        tm=tm,
        redis_client=fake_async_redis,
        config_event=faux_stop_event,
        config=config,
    )
    assert widget.config.use_24_hour_format is True
    await widget.display()
