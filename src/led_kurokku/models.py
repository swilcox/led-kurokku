from datetime import time
from typing import Annotated, Union

from pydantic import BaseModel, Field

from .widgets import ClockWidgetConfig, AlertWidgetConfig, MessageWidgetConfig, AnimationWidgetConfig


class Brightness(BaseModel):
    begin: time = time(8, 0)
    end: time = time(20, 0)
    high: int = 7
    low: int = 2


class ConfigSettings(BaseModel):
    """Configuration settings"""

    widgets: list[
        Annotated[
            Union[ClockWidgetConfig, AlertWidgetConfig, MessageWidgetConfig, AnimationWidgetConfig],
            Field(discriminator="widget_type"),
        ],
    ]
    brightness: Brightness = Brightness()
