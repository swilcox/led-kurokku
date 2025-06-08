import json
import asyncio
import logging
from typing import Dict, List, Optional, Set

from .base_driver import BaseDriver

logger = logging.getLogger(__name__)


class WebSocketDriver(BaseDriver):
    """
    WebSocket driver for TM1637 display.
    Sends display data as JSON over WebSocket connections.
    """

    def __init__(self, brightness=2) -> None:
        """
        Initialize the WebSocket TM1637 driver.
        
        :param brightness: Initial brightness level (0-7).
        """
        super().__init__(brightness=brightness)
        self._driver_name = "websocket"
        self._connected_clients: Set[asyncio.Queue] = set()
        self._current_display = [0, 0, 0, 0]
        self._current_colon = False

    def add_client(self, queue: asyncio.Queue) -> None:
        """
        Add a client to the WebSocket driver.
        
        :param queue: An asyncio Queue to send updates to.
        """
        self._connected_clients.add(queue)
        # Send the current state to the new client
        self._send_update_to_client(queue)
        logger.debug(f"Added client, total clients: {len(self._connected_clients)}")

    def remove_client(self, queue: asyncio.Queue) -> None:
        """
        Remove a client from the WebSocket driver.
        
        :param queue: The asyncio Queue to remove.
        """
        self._connected_clients.discard(queue)
        logger.debug(f"Removed client, remaining clients: {len(self._connected_clients)}")

    def _send_update_to_client(self, queue: asyncio.Queue) -> None:
        """
        Send the current display state to a specific client.
        
        :param queue: The client's asyncio Queue.
        """
        try:
            update = {
                "brightness": self._brightness,
                "digits": self._current_display,
                "colon": self._current_colon
            }
            queue.put_nowait(json.dumps(update))
        except asyncio.QueueFull:
            logger.warning("Client queue full, update not sent")
        except Exception as e:
            logger.error(f"Error sending update to client: {e}")

    def _broadcast_update(self) -> None:
        """
        Broadcast the current display state to all connected clients.
        """
        if not self._connected_clients:
            return
            
        update = {
            "brightness": self._brightness,
            "digits": self._current_display,
            "colon": self._current_colon
        }
        update_json = json.dumps(update)
        
        for queue in list(self._connected_clients):
            try:
                queue.put_nowait(update_json)
            except asyncio.QueueFull:
                logger.warning("Client queue full, update not sent")
            except Exception as e:
                logger.error(f"Error broadcasting update: {e}")
                # Optionally remove problematic clients
                self._connected_clients.discard(queue)

    def display(self, data: List[int], colon: bool = False) -> None:
        """
        Display the given data and broadcast it to all connected clients.
        
        :param data: A list of integers to display (segment values).
        :param colon: Boolean flag whether to display the colon.
        """
        if not isinstance(data, list) or len(data) != 4:
            raise ValueError("Display data must be a list of 4 integers")
            
        self._current_display = data.copy()
        self._current_colon = colon
        
        logger.debug(f"Displaying: {data}, colon: {colon}")
        self._broadcast_update()

    def clear(self) -> None:
        """
        Clear the display and notify all clients.
        """
        self._current_display = [0, 0, 0, 0]
        self._current_colon = False
        
        logger.debug("Clearing display")
        self._broadcast_update()

    @BaseDriver.brightness.setter
    def brightness(self, value: int) -> None:
        """
        Set the brightness level and broadcast the change to all clients.
        
        :param value: The brightness level (0-7).
        """
        if 0 <= value <= 7:
            self._brightness = value
        else:
            raise ValueError("Brightness must be between 0 and 7")
            
        self._broadcast_update()