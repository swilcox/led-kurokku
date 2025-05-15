"""
CLI commands for managing LED-Kurokku alerts.
"""

import click
from typing import Optional

from ..models.instance import load_registry
from ..utils.redis_helpers import run_async, send_alert, list_alerts, clear_alerts


@click.group()
def alert():
    """Manage LED-Kurokku alerts."""
    pass


@alert.command("send")
@click.option("--clock", "-c", required=True, help="Instance name")
@click.argument("message")
@click.option(
    "--ttl", "-t", type=int, default=300, help="Time to live in seconds (default: 300)"
)
@click.option(
    "--duration",
    "-d",
    type=float,
    help="Display duration in seconds (default: message length * 0.4)",
)
@click.option(
    "--priority", "-p", type=int, default=0, help="Alert priority (default: 0)"
)
def send_alert_command(
    clock: str, message: str, ttl: int, duration: Optional[float], priority: int
):
    """Send an alert to an instance."""
    registry = load_registry()

    instance = registry.get_instance(clock)
    if not instance:
        click.echo(f"No instance found with name '{clock}'.")
        return

    # Calculate display duration if not provided
    display_duration = duration if duration is not None else None

    # Send the alert
    success = run_async(send_alert(instance, message, ttl, display_duration, priority))
    if success:
        click.echo(f"Alert sent to '{clock}'.")
    else:
        click.echo(f"Failed to send alert to '{clock}'.")


@alert.command("list")
@click.argument("instance_name")
def list_instance_alerts(instance_name: str):
    """List current alerts on an instance."""
    registry = load_registry()

    instance = registry.get_instance(instance_name)
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        return

    # List the alerts
    alerts = run_async(list_alerts(instance))
    if not alerts:
        click.echo(f"No alerts found for instance '{instance_name}'.")
        return

    click.echo(f"Alerts for instance '{instance_name}':")
    for alert in alerts:
        click.echo(f"  - ID: {alert['id']}")
        click.echo(f"    Message: {alert['message']}")
        click.echo(f"    Timestamp: {alert['timestamp']}")
        click.echo(f"    Priority: {alert['priority']}")
        click.echo(f"    Display Duration: {alert['display_duration']}")
        click.echo("")


@alert.command("clear")
@click.argument("instance_name")
def clear_instance_alerts(instance_name: str):
    """Clear alerts from an instance."""
    registry = load_registry()

    instance = registry.get_instance(instance_name)
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        return

    # Clear the alerts
    count = run_async(clear_alerts(instance))
    click.echo(f"Cleared {count} alerts from instance '{instance_name}'.")