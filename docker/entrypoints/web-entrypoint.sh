#!/bin/bash
set -e

# Display timezone information (for debugging)
echo "Container timezone set to: $(cat /etc/timezone) ($(date +%Z))"
echo "Current time: $(date)"

# Run the web server with the provided arguments
exec web-kurokku "$@"