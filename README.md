# LED Kurokku

The over-powered LED clock for raspberry pis and the TM1637 LED Display.

![animated_gif](./docs/example.gif)

## Overview

LED-Kurokku is a versatile system for controlling TM1637 LED displays with multiple widgets, automated brightness control, and weather integration. The system consists of:

1. **led-kurokku**: Core application that controls the LED display or a virtual text display.
2. **web-kurokku**: Web server for running a kurokku instance as a web page (essentially a web simulator of a TM1637 display).
3. **kurokku-cli**: Command-line tool for managing multiple LED-Kurokku instances and weather configuration and weather server.

See the [Architecture Document](docs/ARCHITECTURE.md) for a detailed system diagram and explanation of how the components work together.

The clock can be configured to show various widgets at specific intervals.

Widget types:
* clock
  * configurable to show either 12/24 hour format.
    * when in 12 hour format (the colon blinks double while PM and single blink during AM).
  * 
* message
  * these can be static messages or dynamically loaded on display from a Redis compatible store. So if you have a separate process updating a temperature reading in redis, you can have a static message that displays that reading. 
* alert
  * these are designed to be shorter lived messages that you only display when they're present.
  * they are loaded from redis and will appear immediately (depending on configuration) once added.
* animation
  * doing silly stuff with the LED display.
  * the configuration is based on integer arrays and timings.

The clock is designed to have its configuration controlled by a server application that writes configuration data to redis.

## Running Locally without an LED Display

### Virtual Text Display

If you don't install the optional `rpi` dependencies or they're not installed correctly, the program will default to a virtual text display.

```text

 ━━   ━━   ━━   ━━
┃  ┃    ┃ ┃    ┃  ┃
         : ━━   ━━
┃  ┃    ┃    ┃ ┃  ┃
 ━━        ━━   ━━
```

### Web Display

You can run LED-Kurokku with a web-based virtual display that shows the TM1637 segments in a browser:

```bash
web-kurokku
```

This will start a web server on port 8080 (by default) with these features:

1. A WebSocket server that broadcasts display updates in real-time
2. A browser-based visualization of the 7-segment display
3. Full integration with the core application event loop
4. Automatic updates from the configured widgets (clock, messages, alerts, etc.)
5. Support for configuration changes through Redis

You can access the virtual display by opening a web browser and navigating to `http://localhost:8080`.

Command options:
- `--host` - Host address to bind to (default: 0.0.0.0)
- `--port` - Port to listen on (default: 8080)
- `--debug` - Enable debug logging
- `--log-file` - Log file path (empty for console logging)

The web display is fully functional and operates just like a physical TM1637 display - it shows the time, messages, alerts, and other widgets according to your configuration. Any changes to the Redis configuration will be immediately reflected on the web display.

### Debug Mode

If you want to do a deeper dive into debugging, you can specify both the `--debug` flag to force `DEBUG` level logging and `--console` to log detailed information about what would have been sent to the display instead of the virtual display or the real display.

Or you can choose to use the virtual or real display but also log debug level output to a file via:
`--debug`
`--log-file=my_log_filename.log`

## Configuration Details

### Redis Keys

#### Configuration

* `kurokku:config` - main configuration stored in JSON string
  * `widgets` - a list of widget configuration objects
    * `widget_type` - one of `clock`, `alert`, `message`, `animation`
    * `enabled` - boolean (defaults to `true`)
    * `duration` - number of seconds to display (defaults to `5`)
    * `cron` - an optional cron string to define when to display (example: `*/10 * * * *` only displays every 10 minutes)
    * *additional widget_type specific configuration options*
  * `brightness` - brightness settings
    * `begin` - time to begin high brightness (e.g. `08:00`)
    * `end` - time to end high brightness and use low (e.g. `20:00`)
    * `high` - value for high brightness (from `0` to `7`)
    * `low` - value for low brightness (from `0` to `7`)

#### Alerts

* `kurokku:alert:*` - alert messages
  * `timestamp` - ISO 8601 timestamp
  * `message` - string message to display
  * `display_duration` - number of seconds to display

#### Weather Data

* `kurokku:weather:temp:*` - weather temperature data (e.g., "72*F")
* `kurokku:weather:alert:*` - weather alerts from NOAA

#### Messages

* `*` - any key (specified key name in the `dynamic_source` field of a `message` widget)
  * raw string text to display

#### Animations

* `*` - any key (specified key name in the `dynamic_source` field of an `animation` widget)
  * `frames` - a list of frame objects
    * `segments` - a list of integers representing the segments to display in each digit
    * `display_duration` - a `float` in seconds (e.g. `.1`)

### Example Configuration

The following example configures:
- widgets
  - alert widget - only displays if there is an alert.
  - clock - the time (in 12 hour format) - for 5 seconds
  - message - dynamically fetching a temperature message from the local redis instance and displaying for 5 seconds
- brightness
  - high brightness (7) starting at 5:40:48
  - low brightness (5) starting at 19:47:35 (7:47:35 PM)

Using the cli to run the weather server, it will update the brightness begin and end times based on sunrise and sunset for the default weather location for each configured kurokku instance.

```YAML
widgets:
- widget_type: alert
  enabled: true
  duration: 0
  scroll_speed: 0.15
  repeat: true
  sleep_before_repeat: 1.0
- widget_type: clock
  enabled: true
  duration: 5
  use_24_hour_format: false
- widget_type: message
  enabled: true
  duration: 5
  message: --*F
  dynamic_source: kurokku:weather:temp:nashville
  scroll_speed: 0.1
  repeat: false
  sleep_before_repeat: 1.0
brightness:
  begin: 05:40:48
  end: '19:47:35'
  high: 7
  low: 5
```

## CLI Tool

The `kurokku-cli` tool provides a way to manage multiple LED-Kurokku instances. See [README-cli.md](docs/README-cli.md) for detailed usage instructions.

Key features:
- Instance management for multiple LED-Kurokku displays
- Configuration management using YAML files
- Alert sending with customizable display duration
- Weather data integration with automatic brightness adjustment
- Template management for reusable configurations

## Running via Docker Compose

See the [Docker](docs/README-docker.md) readme for more information on running a `docker compose` setup.
