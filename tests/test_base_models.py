import pytest
import json

from led_kurokku.widgets.base import WidgetType, WidgetConfig


def test_widget_type_enum():
    # Test ALERT value
    assert WidgetType.ALERT == "alert"
    assert WidgetType.ALERT.value == "alert"
    
    # Test CLOCK value
    assert WidgetType.CLOCK == "clock"
    assert WidgetType.CLOCK.value == "clock"
    
    # Test MESSAGE value
    assert WidgetType.MESSAGE == "message"
    assert WidgetType.MESSAGE.value == "message"
    
    # Test ANIMATION value
    assert WidgetType.ANIMATION == "animation"
    assert WidgetType.ANIMATION.value == "animation"


def test_widget_config_defaults():
    config = WidgetConfig(widget_type=WidgetType.CLOCK)
    assert config.widget_type == WidgetType.CLOCK
    assert config.enabled is True
    assert config.duration == 5


def test_widget_config_custom_values():
    config = WidgetConfig(
        widget_type=WidgetType.MESSAGE,
        enabled=False,
        duration=10
    )
    assert config.widget_type == WidgetType.MESSAGE
    assert config.enabled is False
    assert config.duration == 10


def test_widget_config_from_dict():
    config_dict = {
        "widget_type": "alert",
        "enabled": True,
        "duration": 15
    }
    config = WidgetConfig(**config_dict)
    assert config.widget_type == WidgetType.ALERT
    assert config.enabled is True
    assert config.duration == 15


def test_widget_config_from_json():
    config_json = """
    {
        "widget_type": "animation",
        "enabled": false,
        "duration": 8
    }
    """
    config_dict = json.loads(config_json)
    config = WidgetConfig(**config_dict)
    assert config.widget_type == WidgetType.ANIMATION
    assert config.enabled is False
    assert config.duration == 8


def test_widget_config_validation():
    # Test with invalid widget_type
    with pytest.raises(ValueError):
        WidgetConfig(widget_type="invalid_type")
    
    # Test with invalid duration type
    with pytest.raises(ValueError):
        WidgetConfig(widget_type=WidgetType.CLOCK, duration="not_a_number")
    
    # Test with invalid enabled type
    with pytest.raises(ValueError):
        WidgetConfig(widget_type=WidgetType.CLOCK, enabled="not_a_boolean")