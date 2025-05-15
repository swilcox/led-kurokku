import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import ValidationError

from ... import models  # Updated import path


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def save_yaml_config(config: Dict[str, Any], file_path: str) -> None:
    """Save a configuration to a YAML file."""
    with open(file_path, "w") as f:
        yaml.dump(config, f, sort_keys=False, indent=2)


def validate_config(config_data: Dict[str, Any]) -> Optional[models.ConfigSettings]:
    """Validate a configuration dictionary against the ConfigSettings model."""
    try:
        return models.ConfigSettings.parse_obj(config_data)
    except ValidationError as e:
        print(f"Error validating configuration: {e}")
        return None


def get_templates_dir() -> Path:
    """Return the path to the templates directory."""
    config_dir = Path(os.path.expanduser("~/.config/led-kurokku"))
    templates_dir = config_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir


def list_templates() -> Dict[str, Path]:
    """List all available templates."""
    templates_dir = get_templates_dir()
    templates = {}
    
    for file_path in templates_dir.glob("*.yaml"):
        templates[file_path.stem] = file_path
    
    return templates


def load_template(name: str) -> Optional[Dict[str, Any]]:
    """Load a template by name."""
    templates = list_templates()
    
    if name not in templates:
        print(f"Template '{name}' not found.")
        return None
    
    return load_yaml_config(str(templates[name]))


def save_template(name: str, config: Dict[str, Any]) -> bool:
    """Save a configuration as a template."""
    templates_dir = get_templates_dir()
    file_path = templates_dir / f"{name}.yaml"
    
    try:
        save_yaml_config(config, str(file_path))
        return True
    except Exception as e:
        print(f"Error saving template: {e}")
        return False