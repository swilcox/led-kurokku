# Import base classes
from .base import WidgetType, WidgetConfig, DisplayWidget

# Import widget implementations
from .animation import AnimationWidget, AnimationWidgetConfig
from .alert import AlertWidget, AlertWidgetConfig
from .clock import ClockWidget, ClockWidgetConfig
from .message import MessageWidget, MessageWidgetConfig

# Import factory function
from .factory import widget_factory

# Define what should be exported from this package
__all__ = [
    # Base classes
    "WidgetType",
    "WidgetConfig",
    "DisplayWidget",
    # Widget implementations
    "AnimationWidget",
    "AnimationWidgetConfig",
    "ClockWidget",
    "ClockWidgetConfig",
    "MessageWidget",
    "MessageWidgetConfig",
    "AlertWidget",
    "AlertWidgetConfig",
    # Factory
    "widget_factory",
]
