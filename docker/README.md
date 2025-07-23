# Docker Configuration

This directory contains Docker configurations for the LED-Kurokku project.

## Directory Structure

- `compose/` - Docker Compose files for different deployment scenarios
- `entrypoints/` - Entry point scripts for different services

## Compose Files

### basic.yml
Runs the basic LED-Kurokku setup:
- Redis server
- LED-Kurokku clock service (requires GPIO hardware)

```bash
docker-compose -f docker/compose/basic.yml up
```

### standalone.yml
Runs a complete standalone system without hardware requirements:
- Redis server
- Weather server
- Web server with virtual display (accessible at http://localhost:8080)

```bash
docker-compose -f docker/compose/standalone.yml up
```

### full.yml
Runs all services including hardware-dependent components:
- Redis server
- LED-Kurokku clock service (requires GPIO hardware)
- Weather server
- Web server with virtual display (accessible at http://localhost:8080)

```bash
docker-compose -f docker/compose/full.yml up
```

## Entry Points

- `docker-entrypoint.sh` - Main LED-Kurokku service (GPIO required)
- `weather-entrypoint.sh` - Weather server service
- `web-entrypoint.sh` - Web server with virtual display