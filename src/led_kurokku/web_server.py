import asyncio
import json
import logging
import os
import pathlib
import sys

import aiohttp
from aiohttp import web
import click
import redis.asyncio as redis

from .core import display_widgets, event_listener
from .tm1637 import TM1637
from .tm1637.factory import create_driver, DriverType
from .tm1637.base_driver import BaseDriver
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)

# Directory to serve static files from
STATIC_DIR = pathlib.Path(__file__).parent / "web" / "static"
WEB_TEMPLATE_DIR = pathlib.Path(__file__).parent / "web" / "templates" / "web_kurokku"


class WebServer:
    """
    Web server for LED-Kurokku with WebSocket support.
    Serves a web page with a virtual TM1637 display and
    provides WebSocket connections for real-time updates.
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        driver_type: DriverType = DriverType.WEBSOCKET,
        driver_instance: BaseDriver | None = None,
    ):
        """
        Initialize the web server.

        :param redis_client: Optional Redis client for state management.
        :param driver_type: Type of TM1637 driver to use.
        :param driver_instance: Optional existing driver instance to use.
        """
        self.app = web.Application()
        self.redis_client = redis_client

        # Use the provided driver instance or create a new one
        if driver_instance:
            self.tm1637_driver = driver_instance
        else:
            self.tm1637_driver = create_driver(driver_type=driver_type)

        self.tm1637 = TM1637(driver=self.tm1637_driver)
        self.clients: dict[str, asyncio.Queue] = {}

        # Set up routes
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/ws", self.handle_websocket)

        # Add static route if static directory exists
        if STATIC_DIR.exists() and STATIC_DIR.is_dir():
            self.app.router.add_static("/static", STATIC_DIR)
        else:
            logger.warning(f"Static directory not found: {STATIC_DIR}")
            # Create the directory if it doesn't exist
            STATIC_DIR.mkdir(parents=True, exist_ok=True)

    async def handle_index(self, request: web.Request) -> web.Response:
        """
        Handle requests to the root path by returning the HTML for the virtual display.

        :param request: The web request.
        :return: HTML response with the virtual display page.
        """
        with open(WEB_TEMPLATE_DIR / "index.html", "r") as f:
            # Read the HTML template from the file
            html = f.read()
        return web.Response(text=html, content_type="text/html")

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """
        Handle WebSocket connections for real-time display updates.

        :param request: The web request.
        :return: WebSocket response.
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Create a queue for this client
        client_queue = asyncio.Queue(maxsize=10)
        client_id = id(ws)
        self.clients[client_id] = client_queue

        # Add the client to the TM1637 driver for updates
        self.tm1637_driver.add_client(client_queue)

        # Send initial state to the client
        try:
            # Start the message handling task
            message_handler_task = asyncio.create_task(
                self._handle_messages(ws, client_queue)
            )

            # Handle incoming messages from client (if needed)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        logger.debug(f"Received message from client: {data}")
                        # Handle client messages here if needed
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break

            # Cancel the message handler task when the connection is closed
            message_handler_task.cancel()
            try:
                await message_handler_task
            except asyncio.CancelledError:
                pass

        finally:
            # Clean up when the connection is closed
            self.tm1637_driver.remove_client(client_queue)
            del self.clients[client_id]

        return ws

    async def _handle_messages(self, ws: web.WebSocketResponse, queue: asyncio.Queue):
        """
        Handle messages from the driver to send to the client.

        :param ws: The WebSocket response object.
        :param queue: The client's message queue.
        """
        try:
            while True:
                # Wait for messages from the driver
                message = await queue.get()

                # Send the message to the client
                if not ws.closed:
                    await ws.send_str(message)
                else:
                    break
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            logger.error(f"Error in WebSocket message handler: {e}")

    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """
        Start the web server.

        :param host: Host address to bind to.
        :param port: Port to listen on.
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Web server started at http://{host}:{port}")

        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour (or until interrupted)


async def run_web_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """
    Run the standalone web server (without core event loop integration).
    This is a simpler version that just starts the web server without
    connecting to the core display_widgets functionality.

    :param host: Host address to bind to.
    :param port: Port to listen on.
    """
    # Get Redis configuration from environment variables
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    # Connect to Redis
    async with redis.Redis(host=redis_host, port=redis_port, db=0) as redis_client:
        server = WebServer(redis_client=redis_client)
        await server.start(host=host, port=port)


async def web_event_loop(host: str, port: int):
    """
    Integrated event loop for the web server with the core application logic.
    This combines the web server with the main display_widgets functionality.
    """
    # Get Redis configuration from environment variables
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    # Create queues and events for inter-task communication
    queue = asyncio.Queue()  # Create an asyncio.Queue for inter-task communication
    stop_event = asyncio.Event()  # Create an asyncio.Event to signal stopping
    config_event = asyncio.Event()  # Event to signal configuration updates

    # Create and start the web server
    web_server = WebServer(driver_type=DriverType.WEBSOCKET)
    web_server_task = asyncio.create_task(web_server.start(host=host, port=port))

    async with redis.Redis(host=redis_host, port=redis_port, db=0) as redis_client:
        tasks: list[asyncio.Task] = [
            asyncio.create_task(
                event_listener(redis_client, queue, config_event, stop_event)
            ),
            asyncio.create_task(
                display_widgets(
                    redis_client,
                    queue,
                    config_event,
                    stop_event,
                    force_console=False,
                    driver_type=DriverType.WEBSOCKET,
                    driver_instance=web_server.tm1637_driver,
                )
            ),
            web_server_task,
        ]

        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled, shutting down...")
        finally:
            # Cancel all running tasks when stopping
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to finish cancellation
            await asyncio.gather(*tasks, return_exceptions=True)


@click.command()
@click.option("--host", default="0.0.0.0", help="Host address to bind to")
@click.option("--port", default=8080, type=int, help="Port to listen on")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
@click.option(
    "--log-file", default="", help="Log file path (empty for console logging)"
)
def main(host, port, debug, log_file):
    """Start the LED-Kurokku web server with a virtual TM1637 display."""
    log_level = logging.INFO if not debug else logging.DEBUG
    setup_logging(level=log_level, filename=log_file)

    logger.info(f"Starting LED-Kurokku web server on {host}:{port}")

    try:
        asyncio.run(web_event_loop(host=host, port=port))
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
    except Exception as e:
        logger.exception(f"Web server error: {e}")
        sys.exit(1)
