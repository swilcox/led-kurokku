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

# Run the application with the provided arguments
exec led-kurokku "$@"