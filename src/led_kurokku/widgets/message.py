import logging
from typing import Literal

from .base import DisplayWidget, WidgetConfig


logger = logging.getLogger(__name__)


class MessageWidgetConfig(WidgetConfig):
    """
    Configuration for the MessageWidget.
    """

    widget_type: Literal["message"] = "message"

    message: str = "LED Kurokku"
    dynamic_source: str | None = None
    scroll_speed: float = 0.1
    repeat: bool = False
    sleep_before_repeat: float = 1.0


class MessageWidget(DisplayWidget):
    async def display(
        self,
    ):
        logger.debug(f"MessageWidget started with config: {self.config}")
        while self.okay_to_display():
            message = self.config.message
            if self.config.dynamic_source:
                # Fetch the message from a dynamic source, e.g., Redis
                dynamic_message = await self.redis_client.get(
                    self.config.dynamic_source
                )
                if dynamic_message:
                    message = dynamic_message.decode("utf-8")
                    logger.debug(
                        f"Dynamic message fetched from {self.config.dynamic_source}: {message}"
                    )
                else:
                    logger.warning(f"failed to receive dynamic_message from {self.config.dynamic_source}")
            if len(message) > self.tm.display_length:
                await self.interruptable_scrolled_display(
                    self.tm.show_text,
                    message,
                    scroll_speed=self.config.scroll_speed,
                    repeat=self.config.repeat,
                    sleep_before_repeat=self.config.sleep_before_repeat,
                    duration=self._duration,
                )
            else:
                self.tm.show_text(message)
            if await self._sleep_and_check_stop(self.config.sleep_before_repeat):
                break
