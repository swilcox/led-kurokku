"""
CLI commands for managing LED-Kurokku instances.
"""

import click

from ..models.instance import KurokkuInstance, load_registry, save_registry
from ..utils.redis_helpers import run_async, test_connection


@click.group()
def instances():
    """Manage LED-Kurokku instances."""
    pass


@instances.command("list")
def list_instances():
    """List all configured instances."""
    registry = load_registry()

    if not registry.instances:
        click.echo("No instances configured.")
        return

    click.echo("Configured instances:")
    for instance in registry.instances:
        click.echo(
            f"  - {instance.name}: {instance.host}:{instance.port} - {instance.description}"
        )


@instances.command("add")
@click.argument("name")
@click.argument("host")
@click.option("--port", "-p", type=int, default=6379, help="Redis port (default: 6379)")
@click.option("--description", "-d", help="Description of the instance")
def add_instance(name: str, host: str, port: int, description: str | None):
    """Add a new instance."""
    registry = load_registry()

    # Check if instance with this name already exists
    if registry.get_instance(name):
        click.echo(f"Instance with name '{name}' already exists.")
        return

    # Create the new instance
    instance = KurokkuInstance(
        name=name,
        host=host,
        port=port,
        description=description or "",
    )

    # Test the connection
    if not run_async(test_connection(instance)):
        if not click.confirm(
            f"Could not connect to Redis at {host}:{port}. Add anyway?"
        ):
            return

    # Add the instance to the registry
    registry.add_instance(instance)
    save_registry(registry)
    click.echo(f"Added instance '{name}'.")


@instances.command("remove")
@click.argument("name")
def remove_instance(name: str):
    """Remove an instance."""
    registry = load_registry()

    instance = registry.remove_instance(name)
    if instance:
        save_registry(registry)
        click.echo(f"Removed instance '{name}'.")
    else:
        click.echo(f"No instance found with name '{name}'.")


@instances.command("update")
@click.argument("name")
@click.option("--new-name", "-n", help="New name for the instance")
@click.option("--host", "-h", help="New Redis host")
@click.option("--port", "-p", type=int, help="New Redis port")
@click.option("--description", "-d", help="New description for the instance")
def update_instance(
    name: str,
    new_name: str | None,
    host: str | None,
    port: int | None,
    description: str | None,
):
    """Update an existing instance."""
    registry = load_registry()

    instance = registry.get_instance(name)
    if not instance:
        click.echo(f"No instance found with name '{name}'.")
        return

    # Create the updated instance
    updated_instance = KurokkuInstance(
        name=new_name or instance.name,
        host=host or instance.host,
        port=port or instance.port,
        description=description if description is not None else instance.description,
    )

    # Test the connection if host or port changed
    if (host or port) and not run_async(test_connection(updated_instance)):
        if not click.confirm(
            f"Could not connect to Redis at {updated_instance.host}:{updated_instance.port}. Update anyway?"
        ):
            return

    # Update the instance in the registry
    if new_name and new_name != name:
        registry.remove_instance(name)
        registry.add_instance(updated_instance)
    else:
        registry.update_instance(name, updated_instance)

    save_registry(registry)
    click.echo(f"Updated instance '{name}'.")


@instances.command("show")
@click.argument("name")
def show_instance(name: str):
    """Show details of a specific instance."""
    registry = load_registry()

    instance = registry.get_instance(name)
    if not instance:
        click.echo(f"No instance found with name '{name}'.")
        return

    click.echo(f"Instance: {instance.name}")
    click.echo(f"Host: {instance.host}")
    click.echo(f"Port: {instance.port}")
    click.echo(f"Description: {instance.description}")

    # Test the connection
    if run_async(test_connection(instance)):
        click.echo("Status: Online")
    else:
        click.echo("Status: Offline")