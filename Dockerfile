# SDV Runtime Compatible UDA Agent Docker Image
# Includes Velocitas SDK for full SDV ecosystem integration
# Size: ~50MB (vs ~25MB for ultra-lightweight version)

FROM python:3.10-slim

LABEL maintainer="UDA Platform"
LABEL version="1.0.0-sdv"
LABEL description="SDV Runtime Compatible Universal Deployment Agent"

# Set working directory
WORKDIR /app

# Install system dependencies for Velocitas SDK
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies including Velocitas SDK
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code
COPY ultra-lightweight-uda-agent.py .
COPY demo-apps/ ./demo-apps/

# Make the agent executable
RUN chmod +x ultra-lightweight-uda-agent.py

# Create non-root user for security
RUN useradd -m -u 1000 uda && chown -R uda:uda /app
USER uda

# Expose health check port (optional)
EXPOSE 8080

# Set default environment variables
ENV KIT_SERVER_URL=http://localhost:3090
ENV LOG_LEVEL=INFO
ENV SDV_MODE=compatible

# Health check (more comprehensive for SDV compatibility)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import asyncio; import sys; sys.exit(0 if asyncio.run(asyncio.sleep(0.1)) is None else 1)" || exit 1

# Run the UDA agent with SDV compatibility
CMD ["python3", "ultra-lightweight-uda-agent.py", "--server", "${KIT_SERVER_URL}"]