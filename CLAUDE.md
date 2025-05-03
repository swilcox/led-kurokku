# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_models.py::test_brightness`
- Run tests with coverage: `uv run pytest` (coverage is enabled by default)
- Generate HTML coverage report: `uv run pytest --cov-report=html`
- Install dependencies: `uv sync`
- Install dev dependencies: `uv sync`
- Install RPi dependencies: `uv sync --extra rpi`

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
