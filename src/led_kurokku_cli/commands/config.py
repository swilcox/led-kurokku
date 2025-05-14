"""
CLI commands for managing LED-Kurokku configurations.
"""

import click
import yaml
import json
import difflib
from typing import Optional

from ..models.instance import load_registry
from ..utils.redis_helpers import run_async, set_config, get_config
from ..utils.config_helpers import (
    load_yaml_config,
    validate_config,
    list_templates,
    load_template,
)


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
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
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
        config_str = yaml.dump(
            json.loads(config_settings.json()), sort_keys=False, indent=2
        )
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
    instance_yaml = yaml.dump(
        json.loads(instance_config.json()), sort_keys=False, indent=2
    ).splitlines()
    local_yaml = yaml.dump(
        json.loads(local_config.json()), sort_keys=False, indent=2
    ).splitlines()

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