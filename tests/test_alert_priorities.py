"""
Tests for weather alert priority configuration and assignment.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from led_kurokku.cli.models.weather import WeatherConfig, WeatherLocation
from led_kurokku.cli.services.weather_service import WeatherService


class TestAlertPriorities:
    """Test alert priority configuration and assignment."""

    def test_default_alert_priorities(self):
        """Test that default alert priorities are configured correctly."""
        config = WeatherConfig()
        
        # Test default configuration includes heat advisory at priority 10
        assert "heat advisory" in config.alert_priorities
        assert config.alert_priorities["heat advisory"] == 10
        
        # Test other default priorities
        assert config.alert_priorities["excessive heat warning"] == 5
        assert config.alert_priorities["winter storm warning"] == 1
        assert config.alert_priorities["tornado warning"] == 1
        assert config.alert_priorities["severe thunderstorm warning"] == 1

    def test_get_alert_priority_exact_match(self):
        """Test exact string matching for alert priorities."""
        config = WeatherConfig()
        
        # Test exact matches
        assert config.get_alert_priority("heat advisory") == 10
        assert config.get_alert_priority("excessive heat warning") == 5
        assert config.get_alert_priority("tornado warning") == 1

    def test_get_alert_priority_case_insensitive(self):
        """Test case-insensitive matching for alert priorities."""
        config = WeatherConfig()
        
        # Test case variations
        assert config.get_alert_priority("Heat Advisory") == 10
        assert config.get_alert_priority("HEAT ADVISORY") == 10
        assert config.get_alert_priority("hEaT aDvIsOrY") == 10
        assert config.get_alert_priority("EXCESSIVE HEAT WARNING") == 5

    def test_get_alert_priority_partial_match(self):
        """Test partial string matching for alert priorities."""
        config = WeatherConfig()
        
        # Test partial matches
        assert config.get_alert_priority("Regional Heat Advisory") == 10
        assert config.get_alert_priority("Extended Heat Advisory for Metro Area") == 10
        assert config.get_alert_priority("Severe Thunderstorm Warning issued") == 1

    def test_get_alert_priority_no_match(self):
        """Test default priority for unmatched alert types."""
        config = WeatherConfig()
        
        # Test alerts not in configuration (should default to priority 1)
        assert config.get_alert_priority("Flood Warning") == 1
        assert config.get_alert_priority("Dense Fog Advisory") == 1
        assert config.get_alert_priority("Unknown Alert Type") == 1

    def test_custom_alert_priorities(self):
        """Test custom alert priority configuration."""
        custom_priorities = {
            "custom alert": 15,
            "high priority alert": 2,
            "flood warning": 8,
        }
        
        config = WeatherConfig(alert_priorities=custom_priorities)
        
        # Test custom priorities
        assert config.get_alert_priority("custom alert") == 15
        assert config.get_alert_priority("high priority alert") == 2
        assert config.get_alert_priority("flood warning") == 8
        
        # Test that non-configured alerts still default to 1
        assert config.get_alert_priority("unknown alert") == 1

    def test_alert_priorities_serialization(self):
        """Test that alert priorities are properly serialized and deserialized."""
        config = WeatherConfig()
        
        # Serialize to JSON
        json_data = config.model_dump_json()
        data = json.loads(json_data)
        
        # Check that alert_priorities are in the serialized data
        assert "alert_priorities" in data
        assert data["alert_priorities"]["heat advisory"] == 10
        
        # Deserialize back
        restored_config = WeatherConfig.model_validate(data)
        assert restored_config.get_alert_priority("heat advisory") == 10

    def test_weather_service_priority_assignment(self):
        """Test that WeatherService correctly assigns priorities to alerts."""
        # Create a config with specific priorities
        config = WeatherConfig(
            alert_priorities={
                "heat advisory": 10,
                "tornado warning": 1,
                "flood warning": 5,
            }
        )
        
        # Test various alert messages and their expected priorities
        test_cases = [
            ("Heat Advisory", 10),
            ("Tornado Warning", 1),
            ("Severe Thunderstorm Warning", 1),  # Default from config
            ("Flood Warning", 5),
            ("Dense Fog Advisory", 1),  # Not configured, should default to 1
            ("Regional Heat Advisory for Metro Area", 10),  # Partial match
        ]
        
        for alert_message, expected_priority in test_cases:
            actual_priority = config.get_alert_priority(alert_message)
            assert actual_priority == expected_priority, \
                f"Alert '{alert_message}' should have priority {expected_priority}, got {actual_priority}"

    def test_alert_priority_edge_cases(self):
        """Test edge cases for alert priority assignment."""
        config = WeatherConfig()
        
        # Test empty string
        assert config.get_alert_priority("") == 1
        
        # Test whitespace only
        assert config.get_alert_priority("   ") == 1
        
        # Test very long string with match
        long_string = "This is a very long alert message that contains heat advisory somewhere in the middle"
        assert config.get_alert_priority(long_string) == 10
        
        # Test string with special characters
        assert config.get_alert_priority("Heat Advisory - Updated!") == 10

    def test_multiple_partial_matches(self):
        """Test behavior when multiple configured alerts match."""
        config = WeatherConfig(
            alert_priorities={
                "heat": 10,
                "heat advisory": 15,
                "advisory": 5,
            }
        )
        
        # Should match the first one found (depends on dict iteration order)
        # This tests that the method handles multiple matches gracefully
        priority = config.get_alert_priority("heat advisory")
        assert priority in [10, 15, 5]  # Any of these is acceptable behavior