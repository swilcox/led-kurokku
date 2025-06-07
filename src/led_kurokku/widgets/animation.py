from datetime import datetime
import json
import logging
from typing import Literal

from pydantic import BaseModel
from .base import DisplayWidget, WidgetConfig


logger = logging.getLogger(__name__)


class AnimationFrame(BaseModel):
    segments: list[int]
    duration: float | None = None


class AnimationWidgetConfig(WidgetConfig):
    """
    Configuration for the AnimationWidget.
    """

    widget_type: Literal["animation"] = "animation"

    frames: list[AnimationFrame] = []
    dynamic_source: str | None = None
    scroll_speed: float = 0.1
    repeat: bool = True
    sleep_before_repeat: float = 0.0
    cron_minute: str | None = None


class AnimationWidget(DisplayWidget):
    def check_cron(self):
        """
        Check if the current minute matches the cron expression.
        """
        if self.config.cron_minute is None or self.config.cron_minute in ["", "*"]:
            return True
        if "/" in self.config.cron_minute:
            # Handle cron expressions with step values
            step = int(self.config.cron_minute.split("/")[1])
            if datetime.now().minute % step != 0:
                return False
        elif int(self.config.cron_minute) != datetime.now().minute:
            return False
        return True

    async def display(self):
        logger.debug(f"AnimationWidget started with config: {self.config}")
        if not self.check_cron(self.config.cron_minute):
            logger.debug("Cron minute check failed, skipping display.")
            return
        while self.okay_to_display():
            frames = self.config.frames
            if self.config.dynamic_source:
                if dynamic_frames_raw := await self.redis_client.get(
                    self.config.dynamic_source
                ):
                    try:
                        frames = [
                            AnimationFrame(**f) for f in json.loads(dynamic_frames_raw)
                        ]
                    except Exception as e:
                        logger.error(f"Failed to load dynamic frames: {e}")
            if len(frames):
                for frame in frames:
                    self.tm.display(frame.segments)
                    if await self._sleep_and_check_stop(
                        frame.duration or self.config.scroll_speed
                    ):
                        break  # breaks from frames loop
                if await self._sleep_and_check_stop(self.config.sleep_before_repeat):
                    break  # breaks from while loop
            else:
                break  # don't display an empty animation
