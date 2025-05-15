import json
import asyncio
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from pydantic import BaseModel

from ..models.instance import KurokkuInstance
from ... import models  # Updated import path
from ...widgets.alert import IndividualAlert
from ...core import (
    REDIS_KEY_CONFIG,
    REDIS_KEY_ALERT,
    REDIS_KEY_SEPARATOR,
)


async def connect_to_instance(instance: KurokkuInstance) -> redis.Redis:
    """Connect to a Redis instance."""
    return redis.Redis(
        host=instance.host,
        port=instance.port,
        db=0,
    )


async def test_connection(instance: KurokkuInstance) -> bool:
    """Test if we can connect to a Redis instance."""
    try:
        client = await connect_to_instance(instance)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


async def set_config(instance: KurokkuInstance, config: models.ConfigSettings) -> bool:
    """Set the configuration for an instance."""
    try:
        client = await connect_to_instance(instance)
        config_json = config.json()
        await client.set(REDIS_KEY_CONFIG, config_json)
        await client.close()
        return True
    except Exception as e:
        print(f"Error setting config: {e}")
        return False


async def get_config(instance: KurokkuInstance) -> Optional[models.ConfigSettings]:
    """Get the configuration from an instance."""
    try:
        client = await connect_to_instance(instance)
        config_json = await client.get(REDIS_KEY_CONFIG)
        await client.close()
        
        if not config_json:
            return None
        
        config_dict = json.loads(config_json)
        return models.ConfigSettings.parse_obj(config_dict)
    except Exception as e:
        print(f"Error getting config: {e}")
        return None


async def send_alert(
    instance: KurokkuInstance, 
    message: str, 
    ttl: int = 300, 
    display_duration: Optional[float] = None,
    priority: int = 0,
) -> bool:
    """Send an alert to an instance."""
    try:
        import uuid
        from datetime import datetime
        
        # Calculate display duration if not provided
        if display_duration is None:
            display_duration = len(message) * 0.4
        
        # Create an alert object
        alert_id = str(uuid.uuid4())
        alert = IndividualAlert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            message=message,
            priority=priority,
            display_duration=display_duration,
            delete_after_display=True,
        )
        
        # Connect to Redis
        client = await connect_to_instance(instance)
        
        # Set the alert
        alert_key = f"{REDIS_KEY_ALERT}{REDIS_KEY_SEPARATOR}{alert_id}"
        alert_json = alert.json(exclude={"id"})  # Exclude ID as it's in the key
        
        await client.set(alert_key, alert_json, ex=ttl)
        await client.close()
        
        return True
    except Exception as e:
        print(f"Error sending alert: {e}")
        return False


async def list_alerts(instance: KurokkuInstance) -> List[Dict[str, Any]]:
    """List all alerts for an instance."""
    try:
        client = await connect_to_instance(instance)
        
        # Get all alert keys
        alert_keys = []
        async for key in client.scan_iter(f"{REDIS_KEY_ALERT}{REDIS_KEY_SEPARATOR}*"):
            alert_keys.append(key)
        
        # Get the alerts
        alerts = []
        for key in alert_keys:
            alert_json = await client.get(key)
            if alert_json:
                alert_dict = json.loads(alert_json)
                alert_dict["id"] = key.decode("utf-8").split(REDIS_KEY_SEPARATOR)[-1]
                alerts.append(alert_dict)
        
        await client.close()
        return alerts
    except Exception as e:
        print(f"Error listing alerts: {e}")
        return []


async def clear_alerts(instance: KurokkuInstance) -> int:
    """Clear all alerts for an instance."""
    try:
        client = await connect_to_instance(instance)
        
        # Get all alert keys
        alert_keys = []
        async for key in client.scan_iter(f"{REDIS_KEY_ALERT}{REDIS_KEY_SEPARATOR}*"):
            alert_keys.append(key)
        
        # Delete the alerts
        count = 0
        for key in alert_keys:
            await client.delete(key)
            count += 1
        
        await client.close()
        return count
    except Exception as e:
        print(f"Error clearing alerts: {e}")
        return 0


# Helper function to run an async function
def run_async(coro):
    """Run an async function and return the result."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)