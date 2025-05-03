# LED Kurokku

The over-powered LED clock for raspberry pis and the TM1637 LED Display.

## Overview

The clock can be configured to show various widgets at specific intervals.

Widget types:
* clock
  * configurable to show either 12/24 hour format.
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

If you don't install the optional `rpi` dependencies or they're not installed correctly, the program will default to a virtual text display.

```text

 ━━   ━━   ━━   ━━
┃  ┃    ┃ ┃    ┃  ┃
         : ━━   ━━
┃  ┃    ┃    ┃ ┃  ┃
 ━━        ━━   ━━
```

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

#### Messages

* `*` - any key (specified key name in the `dynamic_source` field of a `message` widget)
  * raw string text to display

#### Animations

* `*` - any key (specified key name in the `dynamic_source` field of an `animation` widget)
  * `frames` - a list of frame objects
    * `segments` - a list of integers representing the segments to display in each digit
    * `display_duration` - a `float` in seconds (e.g. `.1`)

### Example Configuration

*TODO:* example configuration
