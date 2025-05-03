import pytest
import json
from led_kurokku.widgets.alert import IndividualAlert


def test_individual_alert_required_fields():
    # Test with required fields only
    alert = IndividualAlert(
        id="kurokku:alert:1",
        timestamp="2023-05-01T12:30:00Z",
        message="Test alert"
    )
    assert alert.id == "kurokku:alert:1"
    assert alert.timestamp == "2023-05-01T12:30:00Z"
    assert alert.message == "Test alert"
    assert alert.priority == 0  # Default
    assert alert.display_duration == 5.0  # Default
    assert alert.delete_after_display is False  # Default


def test_individual_alert_all_fields():
    alert = IndividualAlert(
        id="kurokku:alert:2",
        timestamp="2023-05-01T12:45:00Z",
        message="Important alert",
        priority=1,
        display_duration=10.0,
        delete_after_display=True
    )
    assert alert.id == "kurokku:alert:2"
    assert alert.timestamp == "2023-05-01T12:45:00Z"
    assert alert.message == "Important alert"
    assert alert.priority == 1
    assert alert.display_duration == 10.0
    assert alert.delete_after_display is True


def test_individual_alert_from_dict():
    alert_dict = {
        "id": "kurokku:alert:3",
        "timestamp": "2023-05-01T13:00:00Z",
        "message": "Dict alert",
        "priority": 2,
        "display_duration": 7.5,
        "delete_after_display": True
    }
    alert = IndividualAlert(**alert_dict)
    assert alert.id == "kurokku:alert:3"
    assert alert.timestamp == "2023-05-01T13:00:00Z"
    assert alert.message == "Dict alert"
    assert alert.priority == 2
    assert alert.display_duration == 7.5
    assert alert.delete_after_display is True


def test_individual_alert_from_json():
    alert_json = """
    {
        "id": "kurokku:alert:4",
        "timestamp": "2023-05-01T13:15:00Z",
        "message": "JSON alert",
        "priority": 3,
        "display_duration": 3.5,
        "delete_after_display": false
    }
    """
    alert_dict = json.loads(alert_json)
    alert = IndividualAlert(**alert_dict)
    assert alert.id == "kurokku:alert:4"
    assert alert.timestamp == "2023-05-01T13:15:00Z"
    assert alert.message == "JSON alert"
    assert alert.priority == 3
    assert alert.display_duration == 3.5
    assert alert.delete_after_display is False


def test_individual_alert_missing_required_fields():
    # Missing timestamp
    with pytest.raises(ValueError):
        IndividualAlert(id="kurokku:alert:5", message="Missing timestamp")
    
    # Missing message
    with pytest.raises(ValueError):
        IndividualAlert(id="kurokku:alert:6", timestamp="2023-05-01T13:30:00Z")
    
    # Missing id
    with pytest.raises(ValueError):
        IndividualAlert(timestamp="2023-05-01T13:30:00Z", message="Missing id")


def test_individual_alert_invalid_priority_type():
    # Invalid priority type
    with pytest.raises(ValueError):
        IndividualAlert(
            id="kurokku:alert:7",
            timestamp="2023-05-01T13:45:00Z",
            message="Invalid priority",
            priority="high"  # Should be int
        )

def test_individual_alert_invalid_duration_type():    
    # Invalid display_duration type
    with pytest.raises(ValueError):
        IndividualAlert(
            id="kurokku:alert:8",
            timestamp="2023-05-01T14:00:00Z",
            message="Invalid duration",
            display_duration="five"  # Should be float
        )
    
def test_individual_alert_invalid_delete_flag():
    # Pydantic v2 may convert string "yes" to boolean
    # Let's use a value that can't be interpreted as boolean
    with pytest.raises(ValueError):
        IndividualAlert(
            id="kurokku:alert:9",
            timestamp="2023-05-01T14:15:00Z",
            message="Invalid delete flag",
            delete_after_display=123  # Should be bool, number isn't valid
        )