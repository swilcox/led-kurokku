# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
LED-Kurokku is a display manager for TM1637 LED displays with three main components:
1. **led-kurokku**: Core application that controls the LED display
2. **kurokku-cli**: CLI tool for managing multiple LED-Kurokku instances and weather data
3. **web-kurokku**: Web server with virtual TM1637 display for browser-based interaction

## Build/Test Commands
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_models.py::test_brightness`
- Run tests with coverage: `uv run pytest` (coverage is enabled by default)
- Generate HTML coverage report: `uv run pytest --cov-report=html`
- Install dependencies: `uv sync`
- Install dev dependencies: `uv sync`
- Install RPi dependencies: `uv sync --extra rpi`

## CLI Tool Usage
- Managing instances: `kurokku-cli instances [add|remove|list|show|update]`
- Managing configurations: `kurokku-cli config [set|get|validate|diff]`
- Managing templates: `kurokku-cli template [list|save|apply]`
- Sending alerts: `kurokku-cli alert [send|list|clear]`
- Weather service: `kurokku-cli weather [add-location|locations|remove-location|set-api-key|set-intervals|show-config|start]`

## Web Server Usage
- Start web server: `web-kurokku [--host HOST] [--port PORT] [--debug] [--log-file FILE]`
- Default: `web-kurokku` (runs on 0.0.0.0:8080)
- Virtual display accessible at: `http://localhost:8080`
- Features: Real-time WebSocket updates, interactive controls, responsive design

## Code Organization
- `led_kurokku/`: Core LED display application
- `led_kurokku/cli/`: CLI tool for remote management
  - `models/`: Pydantic models for the CLI tool
  - `utils/`: Helper utilities including Redis and config operations
- `led_kurokku/web/`: Web server components
  - `templates/`: HTML templates for virtual display
  - `static/`: CSS, JavaScript, and other static assets
- `led_kurokku/tm1637/websocket.py`: WebSocket driver for virtual display
- `led_kurokku/web_server.py`: Main web server implementation

## Code Style Guidelines
- **Imports**: Standard library first, third-party packages second, local imports last
- **Typing**: Use type annotations for all functions and variables
- **Models**: Use Pydantic for data validation and model definitions
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Async**: Use async/await where applicable, especially for I/O operations
- **Error Handling**: Use try/except blocks with specific exceptions
- **Logging**: Use structured logging with named loggers
- **Documentation**: Include docstrings for all public functions and classes
- **Testing**: Write pytest tests for all new features
- **CLI**: Use Click for command-line interfaces
- **Web**: Use aiohttp for async web servers, WebSockets for real-time communication

## Redis Structure
- `kurokku:config`: Main configuration JSON
- `kurokku:alert:*`: Individual alerts
- `kurokku:channel:*`: Control channels
- `kurokku:weather:temp:*`: Weather temperature data
- `kurokku:weather:alert:*`: Weather alerts from NOAA
