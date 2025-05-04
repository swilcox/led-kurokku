FROM python:3.11-slim-buster

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-setuptools \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY docker-entrypoint.sh /usr/local/bin/

# Create non-root user but don't switch to it (we'll control user at runtime)
RUN useradd -m appuser

# Install dependencies including Raspberry Pi specific ones
RUN pip install --no-cache-dir .[rpi] && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# Default command (will run as root by default)
ENTRYPOINT ["docker-entrypoint.sh"]
CMD []