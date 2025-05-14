"""
CLI commands for managing LED-Kurokku configuration templates.
"""

import click
import yaml

from ..utils.config_helpers import (
    load_yaml_config,
    validate_config,
    list_templates,
    load_template,
    save_template
)


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