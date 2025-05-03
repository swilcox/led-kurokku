import json
import logging
from typing import Literal

from pydantic import BaseModel
from .base import DisplayWidget, WidgetConfig


logger = logging.getLogger(__name__)


class AnimationFrame(BaseModel):
    segments: list[int]
    duration: float|None = None


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


class AnimationWidget(DisplayWidget):
    async def display(self):
        logger.debug(f"AnimationWidget started with config: {self.config}")
        while self.okay_to_display():
            frames = self.config.frames
            if self.config.dynamic_source:
                if dynamic_frames_raw := await self.redis_client.get(self.config.dynamic_source):
                    try:
                        frames = [AnimationFrame(**f) for f in json.loads(dynamic_frames_raw)]
                    except Exception as e:
                        logger.error(f"Failed to load dynamic frames: {e}")
            if len(frames):
                for frame in frames:
                    self.tm.display(frame.segments)
                    if await self._sleep_and_check_stop(frame.duration or self.config.scroll_speed):
                        break  # breaks from frames loop
                if await self._sleep_and_check_stop(self.config.sleep_before_repeat):
                    break  # breaks from while loop
            else:
                break  # don't display an empty animation
