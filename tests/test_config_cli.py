import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import yaml
from click.testing import CliRunner

from led_kurokku.cli.commands.config import config
from led_kurokku.cli_main import cli
from led_kurokku.cli.models.instance import KurokkuInstance, KurokkuRegistry
from led_kurokku.models import ConfigSettings


@pytest.fixture
def basic_config_data():
    """Basic configuration data for testing."""
    return {
        "widgets": [{"widget_type": "clock"}, {"widget_type": "alert"}],
        "brightness": {"high": 7, "low": 2, "begin": "08:00", "end": "20:00"},
    }


@pytest.fixture
def temp_config_file(basic_config_data):
    """Create a temporary YAML config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(basic_config_data, f, sort_keys=False, indent=2)
        temp_file = f.name

    yield temp_file

    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def mock_registry():
    """Create a mock registry with a test instance."""
    instance = KurokkuInstance(
        name="test-instance", host="localhost", port=6379, description="Test instance"
    )
    registry = KurokkuRegistry(instances=[instance])
    return registry


@pytest.fixture
def mock_async_functions():
    """Mock async functions used by the config set command."""
    mock_set_config = AsyncMock(return_value=True)

    with (
        patch("led_kurokku.cli.commands.config.run_async") as mock_run_async,
        patch("led_kurokku.cli.commands.config.set_config", mock_set_config),
    ):
        # Make run_async execute the coroutine and return its result
        mock_run_async.side_effect = lambda coro: True

        yield {"run_async": mock_run_async, "set_config": mock_set_config}


def test_config_set_basic_configuration(
    temp_config_file, mock_registry, mock_async_functions
):
    """Test setting a basic configuration for an instance."""
    runner = CliRunner()

    with patch(
        "led_kurokku.cli.commands.config.load_registry", return_value=mock_registry
    ):
        result = runner.invoke(cli, ["config", "set", "test-instance", temp_config_file])

    assert result.exit_code == 0
    assert "Configuration set for instance 'test-instance'." in result.output

    # Verify that set_config was called
    mock_async_functions["set_config"].assert_called_once()

    # Verify the config data passed to set_config
    call_args = mock_async_functions["set_config"].call_args
    instance_arg = call_args[0][0]
    config_arg = call_args[0][1]

    assert instance_arg.name == "test-instance"
    assert isinstance(config_arg, ConfigSettings)
    assert len(config_arg.widgets) == 2
    assert config_arg.widgets[0].widget_type == "clock"
    assert config_arg.widgets[1].widget_type == "alert"
    assert config_arg.brightness.high == 7
    assert config_arg.brightness.low == 2


def test_config_set_nonexistent_instance(temp_config_file):
    """Test setting config for a non-existent instance."""
    runner = CliRunner()
    empty_registry = KurokkuRegistry()

    with patch(
        "led_kurokku.cli.commands.config.load_registry", return_value=empty_registry
    ):
        result = runner.invoke(
            cli, ["config", "set", "nonexistent-instance", temp_config_file]
        )

    assert result.exit_code == 0
    assert "No instance found with name 'nonexistent-instance'." in result.output


def test_config_set_invalid_config_file(mock_registry):
    """Test setting config with an invalid config file."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        # Write invalid configuration
        f.write("invalid: yaml: content: asdf[")
        invalid_file = f.name

    try:
        with patch(
            "led_kurokku.cli.commands.config.load_registry", return_value=mock_registry
        ):
            result = runner.invoke(cli, ["config", "set", "test-instance", invalid_file])
            assert result.exit_code == 1
            assert "Error loading configuration file:" in result.output
    finally:
        os.unlink(invalid_file)


def test_config_set_invalid_config_structure(mock_registry):
    """Test setting config with valid YAML but invalid config structure."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        # Write valid YAML but invalid configuration structure
        yaml.dump({"invalid_field": "some_value", "widgets": "not_a_list"}, f)
        invalid_file = f.name

    try:
        with patch(
            "led_kurokku.cli.commands.config.load_registry", return_value=mock_registry
        ):
            result = runner.invoke(cli, ["config", "set", "test-instance", invalid_file])
            assert result.exit_code == 1
            assert "Invalid configuration file." in result.output
    finally:
        os.unlink(invalid_file)


def test_config_set_failed_redis_operation(temp_config_file, mock_registry):
    """Test handling of failed Redis operations."""
    runner = CliRunner()

    # Mock set_config to return False (failure)
    mock_set_config = AsyncMock(return_value=False)

    with (
        patch(
            "led_kurokku.cli.commands.config.load_registry", return_value=mock_registry
        ),
        patch("led_kurokku.cli.commands.config.run_async", return_value=False),
        patch("led_kurokku.cli.commands.config.set_config", mock_set_config),
    ):
        result = runner.invoke(cli, ["config", "set", "test-instance", temp_config_file])

    assert result.exit_code == 0
    assert "Failed to set configuration for instance 'test-instance'." in result.output


def test_config_set_with_template(
    temp_config_file, mock_registry, mock_async_functions
):
    """Test setting config with a template applied."""
    runner = CliRunner()

    # Mock template data
    template_data = {
        "brightness": {"high": 5, "low": 1, "begin": "07:00", "end": "22:00"},
        "widgets": [{"widget_type": "message"}],
    }

    with (
        patch(
            "led_kurokku.cli.commands.config.load_registry", return_value=mock_registry
        ),
        patch(
            "led_kurokku.cli.commands.config.load_template", return_value=template_data
        ),
    ):
        result = runner.invoke(
            cli,
            ["config", "set", "test-instance", temp_config_file, "--template", "basic-template"],
        )

    assert result.exit_code == 0
    assert "Configuration set for instance 'test-instance'." in result.output

    # Verify that the config merges template with file data
    # File data should override template data
    call_args = mock_async_functions["set_config"].call_args
    config_arg = call_args[0][1]

    # Brightness from file should override template
    assert config_arg.brightness.high == 7
    assert config_arg.brightness.low == 2

    # Widgets from file should override template
    assert len(config_arg.widgets) == 2
    assert config_arg.widgets[0].widget_type == "clock"
    assert config_arg.widgets[1].widget_type == "alert"
