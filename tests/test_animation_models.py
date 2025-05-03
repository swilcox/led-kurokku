import pytest
import json
from led_kurokku.widgets.animation import AnimationFrame


def test_animation_frame_defaults():
    # Test with required segments
    frame = AnimationFrame(segments=[1, 2, 3, 4])
    assert frame.segments == [1, 2, 3, 4]
    assert frame.duration is None


def test_animation_frame_custom_values():
    frame = AnimationFrame(
        segments=[5, 6, 7, 8],
        duration=0.75
    )
    assert frame.segments == [5, 6, 7, 8]
    assert frame.duration == 0.75


def test_animation_frame_from_dict():
    frame_dict = {
        "segments": [1, 2, 3, 4],
        "duration": 0.5
    }
    frame = AnimationFrame(**frame_dict)
    assert frame.segments == [1, 2, 3, 4]
    assert frame.duration == 0.5


def test_animation_frame_from_json():
    frame_json = """
    {
        "segments": [9, 8, 7, 6],
        "duration": 0.25
    }
    """
    frame_dict = json.loads(frame_json)
    frame = AnimationFrame(**frame_dict)
    assert frame.segments == [9, 8, 7, 6]
    assert frame.duration == 0.25


def test_animation_frame_missing_segments():
    # Test with missing segments (required field)
    with pytest.raises(ValueError):
        AnimationFrame()


def test_animation_frame_empty_segments():
    # Empty segments list should be valid
    frame = AnimationFrame(segments=[])
    assert frame.segments == []
    assert frame.duration is None


def test_animation_frame_invalid_segment_type():
    # Segments must be a list of integers
    with pytest.raises(ValueError):
        AnimationFrame(segments=["not", "integers"])


def test_animation_frame_invalid_duration_type():
    # Duration must be a number or None
    with pytest.raises(ValueError):
        AnimationFrame(segments=[1, 2, 3, 4], duration="not_a_number")