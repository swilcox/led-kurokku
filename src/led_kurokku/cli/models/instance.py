from typing import Annotated
import os
import json
from pathlib import Path

from pydantic import BaseModel, Field


class KurokkuInstance(BaseModel):
    """Configuration for a single LED-Kurokku instance."""

    name: Annotated[
        str, Field(min_length=1, description="Unique name for the instance")
    ]
    host: Annotated[
        str, Field(min_length=1, description="Host address of the Redis server")
    ]
    port: int = 6379
    description: str = ""

    def redis_url(self) -> str:
        """Return the Redis URL for this instance."""
        return f"redis://{self.host}:{self.port}"


class KurokkuRegistry(BaseModel):
    """Registry of all LED-Kurokku instances."""

    instances: Annotated[
        list[KurokkuInstance],
        Field(description="List of Kurokku instances", default_factory=list),
    ]

    def add_instance(self, instance: KurokkuInstance) -> None:
        """Add an instance to the registry."""
        # Check if an instance with the same name already exists
        if any(i.name == instance.name for i in self.instances):
            raise ValueError(f"Instance with name '{instance.name}' already exists")

        self.instances.append(instance)

    def remove_instance(self, name: str) -> KurokkuInstance | None:
        """Remove an instance from the registry."""
        for i, instance in enumerate(self.instances):
            if instance.name == name:
                return self.instances.pop(i)
        return None

    def get_instance(self, name: str) -> KurokkuInstance | None:
        """Get an instance by name."""
        for instance in self.instances:
            if instance.name == name:
                return instance
        return None

    def update_instance(self, name: str, new_instance: KurokkuInstance) -> bool:
        """Update an existing instance."""
        for i, instance in enumerate(self.instances):
            if instance.name == name:
                self.instances[i] = new_instance
                return True
        return False


def get_registry_path() -> Path:
    """Return the path to the registry file."""
    config_dir = Path(os.path.expanduser("~/.config/led-kurokku"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "registry.json"


def load_registry() -> KurokkuRegistry:
    """Load the registry from disk."""
    registry_path = get_registry_path()

    if not registry_path.exists():
        return KurokkuRegistry()

    try:
        with open(registry_path, "r") as f:
            data = json.load(f)
        return KurokkuRegistry.model_validate(data)
    except Exception as e:
        # If there's an error loading the registry, return an empty one
        print(f"Error loading registry: {e}")
        return KurokkuRegistry()


def save_registry(registry: KurokkuRegistry) -> None:
    """Save the registry to disk."""
    registry_path = get_registry_path()

    with open(registry_path, "w") as f:
        f.write(registry.model_dump_json())