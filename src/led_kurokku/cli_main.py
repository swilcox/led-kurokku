#!/usr/bin/env python3
import click

from .cli.commands import instances, config, template, alert, weather


# Main CLI entry point
@click.version_option()
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

something = 1
