# LED-Kurokku CLI Tool

A command-line tool for managing multiple LED-Kurokku instances.

## Installation

The CLI tool is included with the LED-Kurokku package. Install it with:

```bash
pip install led-kurokku
```

Or from the repository:

```bash
uv sync
```

## Usage

The `kurokku-cli` command provides the following subcommands:

### Instance Management

Manage LED-Kurokku instances and their Redis connections.

```bash
# List all configured instances
kurokku-cli instances list

# Add a new instance
kurokku-cli instances add "Living Room" living-room.local
kurokku-cli instances add "Kitchen" kitchen.local --port 6380 --description "Kitchen clock"

# Remove an instance
kurokku-cli instances remove "Living Room"

# Update an instance
kurokku-cli instances update "Kitchen" --host kitchen-new.local --port 6379

# Show details of a specific instance
kurokku-cli instances show "Kitchen"
```

### Configuration Management

Manage LED-Kurokku configurations for instances.

```bash
# Set configuration from a YAML file
kurokku-cli config set "Kitchen" kitchen-config.yaml

# Apply a template when setting configuration
kurokku-cli config set "Kitchen" kitchen-config.yaml --template basic-clock

# Get current configuration from an instance
kurokku-cli config get "Kitchen"
kurokku-cli config get "Kitchen" --output kitchen-current.yaml
kurokku-cli config get "Kitchen" --format json

# Validate a YAML configuration file
kurokku-cli config validate config.yaml

# Compare local config with instance config
kurokku-cli config diff "Kitchen" new-config.yaml
```

### Template Management

Manage configuration templates.

```bash
# List all available templates
kurokku-cli template list

# Save a configuration as a template
kurokku-cli template save basic-clock config.yaml

# Apply a template to create a new configuration file
kurokku-cli template apply basic-clock new-config.yaml
```

### Alert Management

Send and manage alerts for LED-Kurokku instances.

```bash
# Send an alert to an instance
kurokku-cli alert send --clock "Kitchen" "Dinner is ready"
kurokku-cli alert send --clock "Kitchen" "Oven timer finished" --ttl 600 --duration 10 --priority 1

# List current alerts on an instance
kurokku-cli alert list "Kitchen"

# Clear alerts from an instance
kurokku-cli alert clear "Kitchen"
```

### Weather Management

Manage weather locations and run the weather service.

```bash
# List all configured weather locations
kurokku-cli weather locations

# Add a new weather location
kurokku-cli weather add-location nashville 36.1627 -86.7816
kurokku-cli weather add-location san_francisco 37.7749 -122.4194 --display-name "San Francisco"

# Remove a weather location
kurokku-cli weather remove-location nashville

# Set the OpenWeather API key
kurokku-cli weather set-api-key "your-api-key-here"

# Set update intervals (in seconds)
kurokku-cli weather set-intervals --temperature 300 --alerts 900

# Show current weather configuration
kurokku-cli weather show-config

# Start the weather service
kurokku-cli weather start
kurokku-cli weather start --debug
```

The weather service fetches:
1. Temperature data from OpenWeather API (formatted for 4-character LED display)
2. Weather alerts from NOAA
3. Sunrise and sunset times to automatically adjust display brightness

This data is distributed to all configured LED-Kurokku instances with appropriate TTLs.

#### Automatic Brightness Adjustment

The weather service automatically updates the brightness settings in each LED-Kurokku instance based on the actual sunrise and sunset times for the configured locations. This ensures that the display is always adjusted to the optimal brightness based on real daylight conditions:

- Display will use high brightness between sunrise and sunset
- Display will use low brightness between sunset and sunrise
- Settings are only updated when the times change by 10 minutes or more

## Configuration Files

The CLI tool stores its configuration in the following locations:

- Registry: `~/.config/led-kurokku/registry.json`
- Templates: `~/.config/led-kurokku/templates/`
- Weather config: `~/.config/led-kurokku/weather_config.json`

## Configuration Format

LED-Kurokku configuration files use YAML format. Here's an example:

```yaml
widgets:
  - widget_type: clock
    enabled: true
    duration: 10
    format: "HH:MM"
    show_seconds: false
    
  - widget_type: alert
    enabled: true
    duration: 0
    scroll_speed: 0.1
    repeat: true
    sleep_before_repeat: 1.0

brightness:
  begin: "08:00"
  end: "20:00"
  high: 7
  low: 2
```

## Template Usage

Templates are predefined configuration files that can be applied or merged with other configurations.

To save the current configuration of an instance as a template:

```bash
kurokku-cli config get "Kitchen" --output temp-config.yaml
kurokku-cli template save kitchen-template temp-config.yaml
```

To apply a template when setting configuration:

```bash
kurokku-cli config set "Living Room" room-specific.yaml --template kitchen-template
```

## Redis Key Format

The CLI uses the following Redis key formats:

- Instance configuration: `kurokku:config`
- Alerts: `kurokku:alert:{alert_id}`
- Weather temperature: `kurokku:weather:temp:{location_name}`
- Weather alerts: `kurokku:weather:alert:{location_name}:{alert_index}`

## Environment Variables

The following environment variables can be used:

- `KUROKKU_CONFIG_DIR`: Override the default config directory (`~/.config/led-kurokku`)
- `OPENWEATHER_API_KEY`: Set the OpenWeather API key (alternative to using the CLI command)