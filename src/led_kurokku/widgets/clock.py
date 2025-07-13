from typing import Literal
from datetime import datetime

from .base import DisplayWidget, WidgetConfig


class ClockWidgetConfig(WidgetConfig):
    """
    Configuration for the ClockWidget.
    """

    widget_type: Literal["clock"] = "clock"
    use_24_hour_format: bool = True


def _convert_to_12_hour_format(hours: int) -> int:
    """Convert 24-hour format to 12-hour format."""
    if hours > 12:
        return hours - 12
    elif hours == 0:
        return 12
    return hours


class ClockWidget(DisplayWidget):
    async def display(self):
        """
        Display method to be overridden by subclasses.
        This method should contain the logic to display the widget's content.
        """

        while self.okay_to_display():
            # Display the current time
            now = datetime.now()
            if not self.config.use_24_hour_format and now.hour >= 12:
                # double blink for PM
                colon_list = [
                    [True, 0.15],
                    [False, 0.2],
                    [True, 0.15],
                    [False, 0.5],
                ]
            else:
                colon_list = [
                    [True, 0.5],
                    [False, 0.5],
                ]
            for colon, timing in colon_list:
                hours = datetime.now().hour
                minutes = datetime.now().minute
                if not self.config.use_24_hour_format:
                    hours = _convert_to_12_hour_format(hours)
                self.tm.show_time(hours, minutes, colon=colon, leading_blank=not self.config.use_24_hour_format)
                if await self._sleep_and_check_stop(timing):
                    break
