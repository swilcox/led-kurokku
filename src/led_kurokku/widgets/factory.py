import asyncio

from redis.asyncio import Redis

from . import AnimationWidget, DisplayWidget
from .alert import AlertWidget
from .base import WidgetType, WidgetConfig
from .clock import ClockWidget
from .message import MessageWidget
from ..tm1637 import TM1637


WIDGET_MAP = {
    WidgetType.ALERT: AlertWidget,
    WidgetType.CLOCK: ClockWidget,
    WidgetType.MESSAGE: MessageWidget,
    WidgetType.ANIMATION: AnimationWidget,
}


def widget_factory(
    config: WidgetConfig,
    tm: TM1637,
    redis_client: Redis,
    config_event: asyncio.Event,
) -> DisplayWidget:
    """Factory function to create a widget based on the configuration."""

    return WIDGET_MAP.get(config.widget_type)(tm, redis_client, config_event, config)
