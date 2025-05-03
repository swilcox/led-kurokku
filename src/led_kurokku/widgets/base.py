import asyncio
from datetime import timedelta
from enum import StrEnum
from datetime import datetime
import logging

from pydantic import BaseModel
from redis.asyncio import Redis

from ..tm1637 import TM1637

logger = logging.getLogger(__name__)


class WidgetType(StrEnum):
    """Widget types"""

    ALERT = "alert"
    CLOCK = "clock"
    MESSAGE = "message"
    ANIMATION = "animation"


class WidgetConfig(BaseModel):
    """Widget configuration"""

    widget_type: WidgetType
    enabled: bool = True
    duration: int = 5  # seconds


class DisplayWidget:
    DEFAULT_DURATION = 5  # Default run time in seconds

    def __init__(
        self,
        tm: TM1637,
        redis_client: Redis = None,
        config_event: asyncio.Event = None,
        config: WidgetConfig = None,
    ):
        """
        Initialize the BaseWidget with.
        :param config_queue: An asyncio.Queue for receiving configuration updates.
        """
        self.config_event = config_event
        self.config = config
        self.tm = tm
        self.redis_client = redis_client
        self._duration = self.config.duration if self.config else self.DEFAULT_DURATION
        self._start_time = None

    async def _sleep_and_check_stop(self, duration):
        """
        Sleep for the specified duration and check if the stop event is set.
        """
        try:
            await asyncio.wait_for(self.config_event.wait(), timeout=duration)
        except asyncio.TimeoutError:
            pass
        return self.config_event.is_set()

    def okay_to_display(self):
        """
        Check if the widget is okay to display.
        This can be overridden by subclasses to implement specific conditions.
        """
        if self._start_time is None:
            self._start_time = datetime.now()
        return (not self.config_event.is_set()) and (
            self._duration <= 0
            or (datetime.now() - self._start_time).seconds < self._duration
        )

    async def interruptable_scrolled_display(
        self,
        display_func,
        message: str,
        scroll_speed=0.1,
        repeat=True,
        sleep_before_repeat=1.0,
        duration=5.0,
    ):
        """
        Display method that allows for scrolling text with interruption.
        :param display_func: The function to call for displaying the text.
        :param scroll_speed: Speed of scrolling.
        :param repeat: Whether to repeat the scrolling.
        :param sleep_before_repeat: Time to wait before repeating the scroll.
        """
        logger.debug("Starting interruptable scrolled display.")
        logger.debug(f"Message: {message}")
        logger.debug(
            f"Scroll speed: {scroll_speed}, Repeat: {repeat}, Sleep before repeat: {sleep_before_repeat}, Duration: {duration}"
        )
        start_time = datetime.now()
        internal_message = (
            " " * self.tm.display_length + message + " " * self.tm.display_length
        )  # Add padding for scrolling
        msg_index = 0

        while self.okay_to_display() and datetime.now() - start_time < timedelta(
            seconds=duration
        ):
            display_func(
                internal_message[msg_index : msg_index + self.tm.display_length]
            )
            if await self._sleep_and_check_stop(scroll_speed):
                break
            msg_index += 1
            if msg_index > len(internal_message) - self.tm.display_length:
                if repeat:
                    msg_index = 0
                    await self._sleep_and_check_stop(sleep_before_repeat)
                else:
                    msg_index = len(internal_message) - self.tm.display_length

    async def display(self):
        """
        Display method to be overridden by subclasses.
        This method should contain the logic to display the widget's content.
        """
        # This is a placeholder method and should be overridden in subclasses
        raise NotImplementedError("Subclasses must implement this method")
