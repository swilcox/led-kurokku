import logging
import json
from typing import Literal

from pydantic import BaseModel

from .base import DisplayWidget, WidgetConfig

logger = logging.getLogger(__name__)


class IndividualAlert(BaseModel):
    """
    Represents an individual alert with a timestamp and message.
    """

    id: str
    timestamp: str  # ISO 8601 format
    message: str
    priority: int = 0  # Default priority, can be used to sort alerts
    display_duration: float = 5.0  # Duration to display each alert
    delete_after_display: bool = False  # Whether to delete the alert after displaying


class AlertWidgetConfig(WidgetConfig):
    """
    Configuration for the AlertWidget.
    """

    widget_type: Literal["alert"] = "alert"
    duration: int = 0
    scroll_speed: float = 0.1
    repeat: bool = True
    sleep_before_repeat: float = 1.0


class AlertWidget(DisplayWidget):
    async def _get_alerts(self) -> list[IndividualAlert]:
        # TODO: replace key pattern with shared configuration
        alert_keys = set()
        async for k in self.redis_client.scan_iter("kurokku:alert:*"):
            alert_keys.add(k)
        if not alert_keys:
            logger.debug("No alert keys found in Redis.")
            return []
        alerts = []
        for k in alert_keys:
            alert_data = await self.redis_client.get(k)
            if alert_data:
                try:
                    alert = IndividualAlert(id=k, **json.loads(alert_data))
                    alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error parsing alert {k}: {e}")
        return alerts

    async def display(
        self,
    ):
        while self.okay_to_display():
            alerts = await self._get_alerts()

            if not alerts:
                logger.debug("No alerts to display.")
                break

            alerts.sort(key=lambda x: (x.priority, x.timestamp))

            for alert in alerts:
                if len(alert.message) <= self.tm.display_length:
                    self.tm.show_text(alert.message)
                    if await self._sleep_and_check_stop(alert.display_duration):
                        break
                else:
                    await self.interruptable_scrolled_display(
                        self.tm.show_text,
                        alert.message,
                        scroll_speed=self.config.scroll_speed,
                        repeat=self.config.repeat,
                        sleep_before_repeat=self.config.sleep_before_repeat,
                        duration=alert.display_duration,
                    )
            break
