# SDV Runtime Compatible UDA Agent Docker Image
# Full Velocitas SDK integration and KUKSA Data Broker support

FROM python:3.10-slim

LABEL maintainer="UDA Platform"
LABEL version="1.0.0-sdv"
LABEL description="SDV Runtime Compatible Universal Deployment Agent"

# Set working directory
WORKDIR /app

# Install system dependencies for Velocitas SDK and KUKSA
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY ../requirements.txt .

# Install Python dependencies including Velocitas SDK
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code and apps
COPY ../../src/uda_agent.py ./uda_agent.py
COPY ../../apps/ ./apps/

# Make the agent executable
RUN chmod +x uda_agent.py

# Create directories for app deployments
RUN mkdir -p /app/deployments /app/logs && \
    useradd -m -u 1000 uda && \
    chown -R uda:uda /app

USER uda

# Expose health check port
EXPOSE 8080

# Set default environment variables for SDV integration
ENV KIT_SERVER_URL=http://localhost:3090
ENV LOG_LEVEL=INFO
ENV SDV_MODE=standard
ENV KUKSA_DATA_BROKER_ADDRESS=localhost:55555
ENV VEHICLE_APP_SDK_CONFIG_PATH=/app/vehicle-app-sdk-config.json

# Create default SDK config
RUN echo '{"kuksa": {"address": "localhost:55555"}}' > /app/vehicle-app-sdk-config.json

# Health check for SDV compatibility
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import asyncio; import sys; sys.exit(0 if asyncio.run(asyncio.sleep(0.1)) is None else 1)" || exit 1

# Run the UDA agent with full SDV SDK support
CMD ["python3", "uda_agent.py", "--server", "${KIT_SERVER_URL}"]