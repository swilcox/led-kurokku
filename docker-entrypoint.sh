#!/bin/bash
set -e

# Fix permissions for GPIO devices if needed
if [ -e /dev/mem ]; then
    chmod 666 /dev/mem || true
fi

if [ -e /dev/gpiomem ]; then
    chmod 666 /dev/gpiomem || true
fi

# Display timezone information (for debugging)
echo "Container timezone set to: $(cat /etc/timezone) ($(date +%Z))"
echo "Current time: $(date)"

# Make sure no stale GPIO exports exist
if [ -d "/sys/class/gpio" ]; then
    # Try to unexport any potentially in-use pins (23 and 24 by default)
    for pin in 23 24; do
        if [ -e "/sys/class/gpio/gpio${pin}" ]; then
            echo "${pin}" > /sys/class/gpio/unexport 2>/dev/null || true
            echo "Cleaned up GPIO ${pin}"
        fi
    done
fi

# Run the application with the provided arguments
exec led-kurokku "$@"