#!/bin/bash

# UDA Docker Build Script
# Build Docker image from config/docker directory

set -e

echo "🐳 Building UDA Docker Image..."

# Check if we're in the right directory
if [ ! -f "src/uda_agent.py" ]; then
    echo "❌ Error: Please run this script from the uda-agent root directory"
    exit 1
fi

# Navigate to docker directory
cd config/docker

echo "📦 Building image with context: ../../"
echo "🏷️  Image name: uda-agent:latest"

# Build Docker image
docker build -t uda-agent:latest ../..

echo "✅ Docker build completed!"
echo ""
echo "🚀 To run the container:"
echo "docker run -d --name uda-agent -e KIT_SERVER_URL=http://localhost:3090 uda-agent:latest"