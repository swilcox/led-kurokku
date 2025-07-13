# LED-Kurokku CLI

LED-Kurokku CLI is a command-line tool for managing multiple LED-Kurokku displays. It provides functionality for:

1. Managing Redis instance configurations
2. Sending configuration updates to displays
3. Sending alerts to displays
4. Managing configuration templates
5. Weather data collection and distribution

## Installation

The CLI tool is included with the LED-Kurokku package. Install it with:

```bash
pip install led-kurokku
```

## Quick Start

### Configure an Instance

First, add a LED-Kurokku instance:

```bash
kurokku-cli instances add "My-Clock" myclock.local
```

### Send an Alert

Send a message to the display:

```bash
kurokku-cli alert send --clock "My-Clock" "Hello World!"
```

### Configure the Display

Create a YAML configuration file (config.yaml):

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

Apply the configuration:

```bash
kurokku-cli config set "My-Clock" config.yaml
```

## Command Groups

The CLI is organized into the following command groups:

- `instances`: Manage LED-Kurokku instance configurations
- `config`: Manage LED-Kurokku display configurations
- `template`: Manage configuration templates
- `alert`: Send and manage alerts
- `weather`: Manage weather locations and run the weather service

## Full Documentation

For detailed documentation on all available commands and options, see the [CLI Documentation](./src/led_kurokku/cli/README.md).