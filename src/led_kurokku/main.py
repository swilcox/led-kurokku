import asyncio
from dataclasses import dataclass
import logging
import os
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
            display_widgets(redis_client, queue, config_event, stop_event, force_console),
        ]
        await asyncio.gather(*tasks)  # Run tasks concurrently


@click.command()
@click.option('--debug', is_flag=True, default=False)
@click.option('--console', is_flag=True, default=False)
@click.option('--log-file', default="")
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
    asyncio.run(event_loop(force_console=console))


if __name__ == "__main__":
    main()
