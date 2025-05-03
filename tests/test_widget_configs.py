import pytest
import json

from led_kurokku.widgets.clock import ClockWidgetConfig
from led_kurokku.widgets.alert import AlertWidgetConfig
from led_kurokku.widgets.message import MessageWidgetConfig
from led_kurokku.widgets.animation import AnimationWidgetConfig


def test_clock_widget_config_defaults():
    config = ClockWidgetConfig()
    assert config.widget_type == "clock"
    assert config.enabled is True
    assert config.duration == 5
    assert config.use_24_hour_format is True


def test_clock_widget_config_custom_values():
    config = ClockWidgetConfig(
        enabled=False,
        duration=10,
        use_24_hour_format=False
    )
    assert config.widget_type == "clock"
    assert config.enabled is False
    assert config.duration == 10
    assert config.use_24_hour_format is False


def test_clock_widget_config_from_json():
    config_json = """
    {
        "widget_type": "clock",
        "enabled": true,
        "duration": 8,
        "use_24_hour_format": false
    }
    """
    config_dict = json.loads(config_json)
    config = ClockWidgetConfig(**config_dict)
    assert config.widget_type == "clock"
    assert config.enabled is True
    assert config.duration == 8
    assert config.use_24_hour_format is False


def test_alert_widget_config_defaults():
    config = AlertWidgetConfig()
    assert config.widget_type == "alert"
    assert config.enabled is True
    assert config.duration == 0
    assert config.scroll_speed == 0.1
    assert config.repeat is True
    assert config.sleep_before_repeat == 1.0


def test_alert_widget_config_custom_values():
    config = AlertWidgetConfig(
        enabled=False,
        duration=10,
        scroll_speed=0.2,
        repeat=False,
        sleep_before_repeat=2.0
    )
    assert config.widget_type == "alert"
    assert config.enabled is False
    assert config.duration == 10
    assert config.scroll_speed == 0.2
    assert config.repeat is False
    assert config.sleep_before_repeat == 2.0


def test_alert_widget_config_from_json():
    config_json = """
    {
        "widget_type": "alert",
        "enabled": true,
        "duration": 8,
        "scroll_speed": 0.3,
        "repeat": false,
        "sleep_before_repeat": 1.5
    }
    """
    config_dict = json.loads(config_json)
    config = AlertWidgetConfig(**config_dict)
    assert config.widget_type == "alert"
    assert config.enabled is True
    assert config.duration == 8
    assert config.scroll_speed == 0.3
    assert config.repeat is False
    assert config.sleep_before_repeat == 1.5


def test_message_widget_config_defaults():
    config = MessageWidgetConfig()
    assert config.widget_type == "message"
    assert config.enabled is True
    assert config.duration == 5
    assert config.message == "LED Kurokku"
    assert config.dynamic_source is None
    assert config.scroll_speed == 0.1
    assert config.repeat is False
    assert config.sleep_before_repeat == 1.0


def test_message_widget_config_custom_values():
    config = MessageWidgetConfig(
        enabled=False,
        duration=10,
        message="Hello World",
        dynamic_source="kurokku:message:test",
        scroll_speed=0.2,
        repeat=True,
        sleep_before_repeat=2.0
    )
    assert config.widget_type == "message"
    assert config.enabled is False
    assert config.duration == 10
    assert config.message == "Hello World"
    assert config.dynamic_source == "kurokku:message:test"
    assert config.scroll_speed == 0.2
    assert config.repeat is True
    assert config.sleep_before_repeat == 2.0


def test_message_widget_config_from_json():
    config_json = """
    {
        "widget_type": "message",
        "enabled": true,
        "duration": 8,
        "message": "Testing",
        "dynamic_source": "kurokku:message:dynamic",
        "scroll_speed": 0.3,
        "repeat": true,
        "sleep_before_repeat": 1.5
    }
    """
    config_dict = json.loads(config_json)
    config = MessageWidgetConfig(**config_dict)
    assert config.widget_type == "message"
    assert config.enabled is True
    assert config.duration == 8
    assert config.message == "Testing"
    assert config.dynamic_source == "kurokku:message:dynamic"
    assert config.scroll_speed == 0.3
    assert config.repeat is True
    assert config.sleep_before_repeat == 1.5


def test_animation_widget_config_defaults():
    config = AnimationWidgetConfig()
    assert config.widget_type == "animation"
    assert config.enabled is True
    assert config.duration == 5
    assert config.frames == []
    assert config.dynamic_source is None
    assert config.scroll_speed == 0.1
    assert config.repeat is True
    assert config.sleep_before_repeat == 0.0


def test_animation_widget_config_custom_values():
    config = AnimationWidgetConfig(
        enabled=False,
        duration=10,
        frames=[{"segments": [1, 2, 3, 4], "duration": 0.5}],
        dynamic_source="kurokku:animation:test",
        scroll_speed=0.2,
        repeat=False,
        sleep_before_repeat=1.0
    )
    assert config.widget_type == "animation"
    assert config.enabled is False
    assert config.duration == 10
    assert len(config.frames) == 1
    assert config.frames[0].segments == [1, 2, 3, 4]
    assert config.frames[0].duration == 0.5
    assert config.dynamic_source == "kurokku:animation:test"
    assert config.scroll_speed == 0.2
    assert config.repeat is False
    assert config.sleep_before_repeat == 1.0


def test_animation_widget_config_from_json():
    config_json = """
    {
        "widget_type": "animation",
        "enabled": true,
        "duration": 8,
        "frames": [
            {"segments": [1, 2, 3, 4], "duration": 0.5},
            {"segments": [4, 3, 2, 1], "duration": 0.3}
        ],
        "dynamic_source": "kurokku:animation:dynamic",
        "scroll_speed": 0.3,
        "repeat": true,
        "sleep_before_repeat": 1.5
    }
    """
    config_dict = json.loads(config_json)
    config = AnimationWidgetConfig(**config_dict)
    assert config.widget_type == "animation"
    assert config.enabled is True
    assert config.duration == 8
    assert len(config.frames) == 2
    assert config.frames[0].segments == [1, 2, 3, 4]
    assert config.frames[0].duration == 0.5
    assert config.frames[1].segments == [4, 3, 2, 1]
    assert config.frames[1].duration == 0.3
    assert config.dynamic_source == "kurokku:animation:dynamic"
    assert config.scroll_speed == 0.3
    assert config.repeat is True
    assert config.sleep_before_repeat == 1.5