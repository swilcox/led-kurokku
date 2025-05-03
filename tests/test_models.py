from datetime import time

import json

from led_kurokku.models import Brightness, ConfigSettings


def test_brightness():
    sample_json_str = """
    {"begin": "08:01", "end": "20:01", "high": 7, "low": 2}
    """
    sample = json.loads(sample_json_str)
    b = Brightness(**sample)
    assert b.high == 7
    assert b.low == 2
    assert b.begin == time(8, 1)
    assert b.end == time(20, 1)

def test_empty_configsettings():
    sample_json_str = """
    {"widgets": []}
    """
    sample = json.loads(sample_json_str)
    c = ConfigSettings(**sample)
    assert c.widgets == []

def test_config_settings():
    sample_json_str = """
    {"widgets": [{"widget_type": "alert"}, {"widget_type": "clock"}, {"widget_type": "message"}, {"widget_type": "animation"}], "brightness": {"high": 9, "low": 1}}
    """
    sample = json.loads(sample_json_str)
    c = ConfigSettings(**sample)
    assert len(c.widgets) == 4
    assert c.widgets[0].widget_type == "alert"
    assert c.widgets[1].widget_type == "clock"
    assert c.widgets[2].widget_type == "message"
    assert c.widgets[3].widget_type == "animation"
    assert c.brightness.high == 9
    assert c.brightness.low == 1
