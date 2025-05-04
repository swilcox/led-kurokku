#!/usr/bin/env python3
import os
import sys
import click
import yaml
import json
from typing import Optional

from .models.instance import KurokkuInstance, load_registry, save_registry
from .utils.redis_helpers import run_async, test_connection, send_alert, set_config, get_config, list_alerts, clear_alerts
from .utils.config_helpers import load_yaml_config, validate_config, list_templates, load_template, save_template

# Instance management commands
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
        click.echo(f"  - {instance.name}: {instance.host}:{instance.port} - {instance.description}")


@instances.command("add")
@click.argument("name")
@click.argument("host")
@click.option("--port", "-p", type=int, default=6379, help="Redis port (default: 6379)")
@click.option("--description", "-d", help="Description of the instance")
def add_instance(name: str, host: str, port: int, description: Optional[str]):
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
        if not click.confirm(f"Could not connect to Redis at {host}:{port}. Add anyway?"):
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
def update_instance(name: str, new_name: Optional[str], host: Optional[str], port: Optional[int], description: Optional[str]):
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
        if not click.confirm(f"Could not connect to Redis at {updated_instance.host}:{updated_instance.port}. Update anyway?"):
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


# Configuration commands
@click.group()
def config():
    """Manage LED-Kurokku configurations."""
    pass


@config.command("set")
@click.argument("instance_name")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--template", "-t", help="Template to apply")
def set_instance_config(instance_name: str, config_file: str, template: Optional[str]):
    """Set configuration from a YAML file."""
    registry = load_registry()
    
    instance = registry.get_instance(instance_name)
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        return
    
    # Load the config file
    config_data = load_yaml_config(config_file)
    
    # Apply template if specified
    if template:
        template_data = load_template(template)
        if template_data:
            # Merge the template with the config
            config_data = {**template_data, **config_data}
    
    # Validate the config
    config_settings = validate_config(config_data)
    if not config_settings:
        click.echo("Invalid configuration.")
        return
    
    # Set the config
    success = run_async(set_config(instance, config_settings))
    if success:
        click.echo(f"Configuration set for instance '{instance_name}'.")
    else:
        click.echo(f"Failed to set configuration for instance '{instance_name}'.")


@config.command("get")
@click.argument("instance_name")
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")
def get_instance_config(instance_name: str, output: Optional[str], format: str):
    """Get current configuration from an instance."""
    registry = load_registry()
    
    instance = registry.get_instance(instance_name)
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        return
    
    # Get the config
    config_settings = run_async(get_config(instance))
    if not config_settings:
        click.echo(f"No configuration found for instance '{instance_name}'.")
        return
    
    # Output the config
    if format == "yaml":
        config_str = yaml.dump(json.loads(config_settings.json()), sort_keys=False, indent=2)
    else:
        config_str = config_settings.json(indent=2)
    
    if output:
        with open(output, "w") as f:
            f.write(config_str)
        click.echo(f"Configuration written to '{output}'.")
    else:
        click.echo(config_str)


@config.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def validate_config_file(config_file: str):
    """Validate a YAML configuration file."""
    # Load the config file
    config_data = load_yaml_config(config_file)
    
    # Validate the config
    config_settings = validate_config(config_data)
    if config_settings:
        click.echo("Configuration is valid.")
    else:
        click.echo("Configuration is invalid.")


@config.command("diff")
@click.argument("instance_name")
@click.argument("config_file", type=click.Path(exists=True))
def diff_configs(instance_name: str, config_file: str):
    """Compare local config with instance config."""
    import difflib
    
    registry = load_registry()
    
    instance = registry.get_instance(instance_name)
    if not instance:
        click.echo(f"No instance found with name '{instance_name}'.")
        return
    
    # Get the instance config
    instance_config = run_async(get_config(instance))
    if not instance_config:
        click.echo(f"No configuration found for instance '{instance_name}'.")
        return
    
    # Load the local config
    local_config_data = load_yaml_config(config_file)
    local_config = validate_config(local_config_data)
    if not local_config:
        click.echo("Invalid local configuration.")
        return
    
    # Convert to YAML for diffing
    instance_yaml = yaml.dump(json.loads(instance_config.json()), sort_keys=False, indent=2).splitlines()
    local_yaml = yaml.dump(json.loads(local_config.json()), sort_keys=False, indent=2).splitlines()
    
    # Generate the diff
    diff = difflib.unified_diff(
        instance_yaml,
        local_yaml,
        fromfile=f"{instance_name} (remote)",
        tofile=config_file,
        lineterm="",
    )
    
    # Print the diff
    diff_output = "\n".join(diff)
    if diff_output:
        click.echo(diff_output)
    else:
        click.echo("No differences found.")


# Template commands
@click.group()
def template():
    """Manage configuration templates."""
    pass


@template.command("list")
def list_all_templates():
    """List all available templates."""
    templates = list_templates()
    
    if not templates:
        click.echo("No templates available.")
        return
    
    click.echo("Available templates:")
    for name, path in templates.items():
        click.echo(f"  - {name}")


@template.command("save")
@click.argument("name")
@click.argument("config_file", type=click.Path(exists=True))
def save_template_command(name: str, config_file: str):
    """Save a configuration as a template."""
    # Load the config file
    config_data = load_yaml_config(config_file)
    
    # Validate the config
    config_settings = validate_config(config_data)
    if not config_settings:
        click.echo("Invalid configuration.")
        return
    
    # Save the template
    success = save_template(name, config_data)
    if success:
        click.echo(f"Template '{name}' saved.")
    else:
        click.echo(f"Failed to save template '{name}'.")


@template.command("apply")
@click.argument("name")
@click.argument("output_file", type=click.Path())
def apply_template_command(name: str, output_file: str):
    """Apply a template to create a new configuration file."""
    # Load the template
    template_data = load_template(name)
    if not template_data:
        return
    
    # Save the template to the output file
    try:
        with open(output_file, "w") as f:
            yaml.dump(template_data, f, sort_keys=False, indent=2)
        click.echo(f"Template '{name}' applied to '{output_file}'.")
    except Exception as e:
        click.echo(f"Error applying template: {e}")


# Alert commands
@click.group()
def alert():
    """Manage LED-Kurokku alerts."""
    pass


@alert.command("send")
@click.option("--clock", "-c", required=True, help="Instance name")
@click.argument("message")
@click.option("--ttl", "-t", type=int, default=300, help="Time to live in seconds (default: 300)")
@click.option("--duration", "-d", type=float, help="Display duration in seconds (default: message length * 0.4)")
@click.option("--priority", "-p", type=int, default=0, help="Alert priority (default: 0)")
def send_alert_command(clock: str, message: str, ttl: int, duration: Optional[float], priority: int):
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


# Weather commands
from .commands.weather import weather

# Main CLI entry point
@click.group()
def cli():
    """LED-Kurokku CLI tool for managing multiple instances."""
    pass


cli.add_command(instances)
cli.add_command(config)
cli.add_command(template)
cli.add_command(alert)
cli.add_command(weather)


if __name__ == "__main__":
    cli()