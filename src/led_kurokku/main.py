import asyncio
import atexit
from dataclasses import dataclass
import logging
import os
import signal
import sys
from typing import Annotated

import click

from .core import display_widgets, event_listener
from .utils.logging import setup_logging
import redis.asyncio as redis


async def event_loop(force_console=False):
    """
    Event loop function to run the clock application.
    """

    queue = asyncio.Queue()  # Create an asyncio.Queue for inter-task communication
    stop_event = asyncio.Event()  # Create an asyncio.Event to signal stopping
    config_event = asyncio.Event()  # Event to signal configuration updates

    # Get Redis configuration from environment variables
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    async with redis.Redis(host=redis_host, port=redis_port, db=0) as redis_client:
        tasks = [
            event_listener(redis_client, queue, config_event, stop_event),
            display_widgets(
                redis_client, queue, config_event, stop_event, force_console
            ),
        ]
        await asyncio.gather(*tasks)  # Run tasks concurrently


def cleanup_gpio():
    """
    Clean up GPIO pins on application exit.
    This function will be called when the application exits.
    """
    try:
        # Only import GPIO module if it's available
        import importlib.util

        if importlib.util.find_spec("RPi") and importlib.util.find_spec("RPi.GPIO"):
            from RPi import GPIO

            GPIO.cleanup()
            logging.info("GPIO pins cleaned up")
    except Exception as e:
        logging.error(f"Error cleaning up GPIO: {e}")


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""

    def signal_handler(sig, frame):
        logging.info(f"Received signal {sig}, shutting down...")
        cleanup_gpio()
        sys.exit(0)

    # Register signal handlers for common termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


@click.command()
@click.version_option()
@click.option("--debug", is_flag=True, default=False)
@click.option("--console", is_flag=True, default=False)
@click.option("--log-file", default="")
def main(debug, console, log_file):
    """
    Main function to run the clock application.
    """
    # TODO: configurable logging level and whether to go to_file or not.
    log_level = logging.INFO if not debug else logging.DEBUG
    if console:
        log_file = ""  # don't log to file if forcing to console
    setup_logging(level=log_level, filename=log_file)
    logger = logging.getLogger(__name__)
    logger.info("Starting led-kurokku application")

    # Register cleanup functions
    setup_signal_handlers()
    atexit.register(cleanup_gpio)

    try:
        asyncio.run(event_loop(force_console=console))
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception(f"Application error: {e}")
    finally:
        # Make sure GPIO is cleaned up, even if we failed to register the signal handlers
        cleanup_gpio()


if __name__ == "__main__":
    main()
