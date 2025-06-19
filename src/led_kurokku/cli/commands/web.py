import asyncio
import logging
import os
import sys

import click
import redis.asyncio as redis

from ...core import display_widgets, event_listener
from ...tm1637.factory import DriverType
from ...web_server import WebServer
from ...utils.logging import setup_logging


logger = logging.getLogger(__name__)


@click.group()
def web():
    """Manage the LED-Kurokku web server."""
    pass


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


@web.command()
@click.option("--host", default="0.0.0.0", help="Host address to bind to")
@click.option("--port", default=8080, type=int, help="Port to listen on")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
@click.option(
    "--log-file", default="", help="Log file path (empty for console logging)"
)
def start(host, port, debug, log_file):
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
