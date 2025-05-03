import asyncio
from datetime import datetime
import hashlib
import json
import logging

import redis.asyncio as redis
from .models import ConfigSettings
from .tm1637 import TM1637
from .tm1637.factory import create_driver

from .widgets import widget_factory


STOP_WORD = "STOP"  # Define a stop word for the PubSub channel
ALERT_WORD = "ALERT"  # Define an alert word for the PubSub channel

REDIS_KEY_BASE = "kurokku"
REDIS_KEY_SEPARATOR = ":"
REDIS_KEY_CONFIG = f"{REDIS_KEY_BASE}{REDIS_KEY_SEPARATOR}config"
REDIS_KEY_ALERT = f"{REDIS_KEY_BASE}{REDIS_KEY_SEPARATOR}alert"
REDIS_CHANNEL_PATTERN = (
    f"{REDIS_KEY_BASE}{REDIS_KEY_SEPARATOR}channel{REDIS_KEY_SEPARATOR}*"
)
REDIS_CONFIG_EVENT = "__keyspace@0__:" + REDIS_KEY_CONFIG + "*"
REDIS_ALERT_EVENT = "__keyspace@0__:" + REDIS_KEY_ALERT + "*"


logger = logging.getLogger(__name__)


async def display_widgets(
    redis_client: redis.Redis,
    queue: asyncio.Queue,
    config_event: asyncio.Event,
    stop_event: asyncio.Event,
    force_console: bool = False,
):
    """
    Main function to display the clock and other widgets.
    This function should be run in an asynchronous context.
    """
    config_data = ConfigSettings(**(await queue.get()))
    config_event.clear()

    tm = TM1637(driver=create_driver(force_console=force_console))

    while True:
        if config_data.brightness.end > datetime.now().time() > config_data.brightness.begin:
            tm.brightness = config_data.brightness.high
        else:
            tm.brightness = config_data.brightness.low
        for widget_config in config_data.widgets:
            if config_event.is_set() or stop_event.is_set():
                break
            if widget_config.enabled:
                widget = widget_factory(widget_config, tm, redis_client, config_event)
                logger.debug(f"Displaying widget: {widget_config.widget_type}")
                await widget.display()
        if config_event.is_set() and not stop_event.is_set():
            config_data = ConfigSettings(**(await queue.get()))
            config_event.clear()
        if stop_event.is_set():
            logger.debug("Stopping display widgets due to stop event.")
            break


async def event_listener(
    redis_client: redis.Redis,
    queue: asyncio.Queue,
    config_event: asyncio.Event,
    stop_event: asyncio.Event,
):
    await redis_client.config_set("notify-keyspace-events", "KEA")
    config_data = json.loads(await redis_client.get(REDIS_KEY_CONFIG))
    hash_value = (
        hashlib.md5(json.dumps(config_data).encode("utf-8")).hexdigest()
        if config_data
        else None
    )
    # TODO: what to do if hash_value is None?
    logger.info(f"Loaded initial configuration from redis")
    logger.debug(f"Initial configuration hash: {hash_value}")
    logger.debug(f"Initial configuration value: {config_data}")
    config_event.set()
    await queue.put(config_data)
    logger.debug(
        f"Listening for messages on Redis channel pattern: {REDIS_CHANNEL_PATTERN}"
    )
    logger.debug(f"Listening for config updates on Redis key: {REDIS_CONFIG_EVENT}")
    logger.debug(f"Listening for alert updates on Redis key: {REDIS_ALERT_EVENT}")
    async with redis_client.pubsub() as pubsub:
        await pubsub.psubscribe(
            REDIS_CHANNEL_PATTERN, REDIS_ALERT_EVENT, REDIS_CONFIG_EVENT
        )
        logger.info("Entering listening loop for Redis event messages.")
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message is not None:
                logger.debug(f"(Reader) Message Received: {message}")
                data = message.get("data").decode("utf-8", errors="ignore")
                pattern = message.get("pattern").decode("utf-8", errors="ignore")
                if pattern == REDIS_CONFIG_EVENT:
                    logger.debug("Config update redis key event received")
                    new_config_data = json.loads(
                        await redis_client.get(REDIS_KEY_CONFIG)
                    )
                    new_hash_value = (
                        hashlib.md5(
                            json.dumps(new_config_data).encode("utf-8")
                        ).hexdigest()
                        if new_config_data
                        else None
                    )
                    if new_hash_value != hash_value:
                        logger.debug(
                            f"New configuration hash: {new_hash_value}"
                        )
                        logger.debug(f"New configuration value: {new_config_data}")
                        hash_value = new_hash_value
                        config_data = new_config_data
                        logger.info("Configuration update received")
                        config_event.set()
                        await queue.put(new_config_data)
                elif pattern == REDIS_ALERT_EVENT:
                    logger.info("Alert key event received")
                    config_event.set()
                    await queue.put(config_data)
                elif pattern == REDIS_CHANNEL_PATTERN:
                    logger.info("Channel pattern received")
                    if data == STOP_WORD:
                        logger.debug("STOP word seen")
                        logger.debug("Stopping display widgets due to stop word.")
                        config_event.set()
                        stop_event.set()
                        break
                    elif data == ALERT_WORD:
                        logger.debug("ALERT received, stopping display widgets and restarting.")
                        config_event.set()
                else:
                    logger.warning(f"Unhandled redis event pattern: {pattern}")

            await asyncio.sleep(0.1)
