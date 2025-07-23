#!/bin/bash
set -e

# Display timezone information (for debugging)
echo "Container timezone set to: $(cat /etc/timezone) ($(date +%Z))"
echo "Current time: $(date)"

# Run the weather server with the provided arguments
exec kurokku-cli weather start "$@"