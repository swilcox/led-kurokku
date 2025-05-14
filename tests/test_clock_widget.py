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
