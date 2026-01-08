"""WebSocket driver for HT16K33 14-segment displays.

Broadcasts display updates to connected WebSocket clients as JSON.
"""

import asyncio
import json
import logging
from typing import Set

from ..tm1637.base_driver import BaseDriver

logger = logging.getLogger(__name__)


class HT16K33WebSocketDriver(BaseDriver):
    """
    WebSocket driver for HT16K33 14-segment display.

    Sends display data as JSON over WebSocket connections for web-based virtual displays.
    Includes "display_type" field to differentiate from TM1637 displays.
    """

    def __init__(self, brightness: int = 2):
        """
        Initialize the HT16K33 WebSocket driver.

        :param brightness: Initial brightness level (0-7).
        """
        super().__init__(brightness=brightness)
        self._driver_name = "HT16K33-websocket"
        self._connected_clients: Set[asyncio.Queue] = set()
        self._current_display = [0, 0, 0, 0]
        self._current_colon = False

    def add_client(self, queue: asyncio.Queue) -> None:
        """
        Add a WebSocket client queue to receive updates.

        :param queue: Asyncio queue for sending updates to the client.
        """
        self._connected_clients.add(queue)
        self._send_update_to_client(queue)
        logger.debug(f"Added WebSocket client, total: {len(self._connected_clients)}")

    def remove_client(self, queue: asyncio.Queue) -> None:
        """
        Remove a WebSocket client queue.

        :param queue: Asyncio queue to remove.
        """
        self._connected_clients.discard(queue)
        logger.debug(f"Removed WebSocket client, remaining: {len(self._connected_clients)}")

    def _send_update_to_client(self, queue: asyncio.Queue) -> None:
        """
        Send current display state to a specific client.

        :param queue: Client queue to send update to.
        """
        try:
            update = {
                "display_type": "ht16k33",  # Indicates 14-segment display
                "brightness": self._brightness,
                "digits": self._current_display,
                "colon": self._current_colon,
            }
            queue.put_nowait(json.dumps(update))
        except Exception as e:
            logger.error(f"Error sending update to client: {e}")

    def _broadcast_update(self) -> None:
        """Broadcast current display state to all connected clients."""
        if not self._connected_clients:
            return

        update = {
            "display_type": "ht16k33",  # Indicates 14-segment display
            "brightness": self._brightness,
            "digits": self._current_display,
            "colon": self._current_colon,
        }
        update_json = json.dumps(update)

        for queue in list(self._connected_clients):
            try:
                queue.put_nowait(update_json)
            except asyncio.QueueFull:
                logger.warning("Client queue full, update not sent")
            except Exception as e:
                logger.error(f"Error broadcasting update: {e}")
                self._connected_clients.discard(queue)

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display data and broadcast to all connected WebSocket clients.

        :param data: A list of 4 integers representing 14-segment values.
        :param colon: Boolean flag for colon display.
        """
        if not isinstance(data, list) or len(data) != 4:
            raise ValueError("Display data must be a list of 4 integers")

        self._current_display = data.copy()
        self._current_colon = colon

        logger.debug(f"HT16K33 Displaying: {data}, colon: {colon}")
        self._broadcast_update()

    def clear(self) -> None:
        """Clear the display and notify all connected clients."""
        self._current_display = [0, 0, 0, 0]
        self._current_colon = False

        logger.debug("HT16K33 Clearing display")
        self._broadcast_update()

    @BaseDriver.brightness.setter
    def brightness(self, value: int) -> None:
        """
        Set brightness level and broadcast update to clients.

        :param value: Brightness level (0-7).
        """
        if 0 <= value <= 7:
            self._brightness = value
        else:
            raise ValueError("Brightness must be between 0 and 7")

        self._broadcast_update()
