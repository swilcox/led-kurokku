# Running LED Kurokku in Docker on Raspberry Pi

This guide explains how to run LED Kurokku in a Docker container on a Raspberry Pi with proper GPIO passthrough.

## Prerequisites

1. Raspberry Pi (3 or newer recommended) with Raspberry Pi OS (or compatible)
2. Docker and Docker Compose installed on your Pi:
   ```bash
   curl -sSL https://get.docker.com | sh
   sudo apt-get install docker-compose
   sudo usermod -aG docker $USER  # Add your user to docker group
   # Log out and back in for group changes to take effect
   ```
3. TM1637 LED display connected to your Raspberry Pi:
   - Connect CLK to GPIO23 (pin 16)
   - Connect DIO to GPIO24 (pin 18)
   - Connect VCC to 5V
   - Connect GND to Ground

## Building and Running the Container

1. Clone this repository to your Raspberry Pi:
   ```bash
   git clone <repository-url>
   cd led-kurokku
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f led-kurokku
   ```

4. Stop the containers:
   ```bash
   docker-compose down
   ```

## GPIO Passthrough Explanation

The Docker container is configured with direct access to the Raspberry Pi's GPIO system through:

1. Device mapping `/dev/gpiomem` and `/dev/mem` to allow direct memory access
2. Running in privileged mode to allow hardware access

These permissions are required for the RPi.GPIO module to function properly within the container.

## Customizing the Container

### Custom GPIO Pins

If you want to use different GPIO pins than the default (CLK=23, DIO=24), you can add environment variables to the `docker-compose.yml` file:

```yaml
services:
  led-kurokku:
    # ... existing configuration
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CLK_PIN=17  # Use GPIO17 instead of default
      - DIO_PIN=27  # Use GPIO27 instead of default
```

### Setting the Correct Timezone

By default, the container uses the timezone configured in the `docker-compose.yml` file (America/New_York). To change it:

1. Edit the TZ environment variable in `docker-compose.yml`:
   ```yaml
   environment:
     - TZ=Europe/London  # Change to your timezone
   ```

2. Common timezone values:
   - America/New_York
   - America/Los_Angeles
   - Europe/London
   - Europe/Berlin
   - Asia/Tokyo
   - Australia/Sydney

3. For a complete list of timezone names, see the [IANA timezone database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

The container also mounts the host's timezone configuration files, so if your Raspberry Pi is set to the correct timezone, the container should inherit it.

## Troubleshooting

1. **No Display Output**:
   - Check physical connections between Pi and TM1637 display
   - Verify that `/dev/gpiomem` exists and is accessible
   - Try running with `--console` flag to debug: `docker-compose run led-kurokku --console`

2. **"No access to /dev/mem" or Permission Denied Errors**:
   - Ensure container is running as root (`user: root` in docker-compose.yml)
   - Verify both privileged mode and SYS_RAWIO capability are added
   - Make sure both `/dev/gpiomem` and `/dev/mem` are properly mapped
   - On some systems, you may need to adjust permissions: `sudo chmod 666 /dev/mem /dev/gpiomem`

3. **Redis Connection Issues**:
   - Check if Redis container is running: `docker-compose ps`
   - Verify Redis is accessible: `docker-compose exec redis redis-cli ping`

4. **GPIO Import Errors**:
   - The container should automatically fall back to virtual display mode
   - Check that RPi.GPIO is installed: `docker-compose exec led-kurokku pip list | grep RPi`

## Production Deployment

For production use, consider:

1. Using Docker's restart policies:
   ```yaml
   restart: always  # Instead of unless-stopped
   ```

2. Setting up proper logging:
   ```yaml
   command: --log-file=/app/logs/kurokku.log
   volumes:
     - ./logs:/app/logs
   ```

3. Adding healthchecks to automatically restart failing containers:
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('redis', 6379)); s.close()"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```