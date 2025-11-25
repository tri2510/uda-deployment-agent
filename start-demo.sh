#!/bin/bash

# SDV Runtime Compatible UDA Demo Setup Script
# One-command demo of Universal Deployment Agent with SDV ecosystem integration

set -e

echo "🚀 Starting SDV Runtime Compatible UDA Demo Setup..."

# Check if we're in the right directory
if [ ! -f "ultra-lightweight-uda-agent.py" ]; then
    echo "❌ Error: Please run this script from the uda-agent directory"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required networks exist
echo "📡 Setting up Docker networks..."
docker network inspect dreamkit-network > /dev/null 2>&1 || docker network create dreamkit-network

echo "🐳 Building SDV Compatible UDA Agent Docker image..."
docker build -t uda-agent:sdv-compatible .

echo "🏗️ Starting SDV compatible demo environment..."

# Start KUKSA Data Broker (if not running)
if ! docker ps | grep -q "dreamkit-sdv-runtime"; then
    echo "🚗 Starting KUKSA Data Broker..."
    docker run -d \
        --name dreamkit-sdv-runtime \
        --network dreamkit-network \
        -p 55555:55555 \
        ghcr.io/eclipse-autowrx/sdv-runtime:latest || \
    echo "⚠️ KUKSA Data Broker might already be running elsewhere"
fi

# Start Kit Server Adapter (if not running)
if ! docker ps | grep -q "dreamkit-kit-adapter"; then
    echo "🔗 Starting Kit Server Adapter..."
    docker run -d \
        --name dreamkit-kit-adapter \
        --network dreamkit-network \
        -p 3090:3090 \
        ghcr.io/tri2510/kit-server-adapter:latest || \
    echo "⚠️ Kit Server Adapter might already be running elsewhere"
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Test KUKSA connection
echo "🔍 Testing KUKSA Data Broker connection..."
for i in {1..15}; do
    if curl -s http://localhost:55555/vss/api/v1/status > /dev/null 2>&1; then
        echo "✅ KUKSA Data Broker is ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "⚠️ KUKSA Data Broker connection test failed, but continuing..."
    fi
    sleep 2
done

# Test Kit Server Adapter connection
echo "🔍 Testing Kit Server Adapter connection..."
for i in {1..15}; do
    if curl -s http://localhost:3090/health > /dev/null 2>&1; then
        echo "✅ Kit Server Adapter is ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "⚠️ Kit Server Adapter connection test failed, but continuing..."
    fi
    sleep 2
done

# Start SDV Compatible UDA Agent
echo "🤖 Starting SDV Compatible UDA Agent..."
docker run -d \
    --name uda-agent-sdv-demo \
    --network dreamkit-network \
    -e KIT_SERVER_URL=http://dreamkit-kit-adapter:3090 \
    -e SDV_MODE=compatible \
    uda-agent:sdv-compatible

echo "⏳ Waiting for UDA Agent to connect..."
sleep 10

# Show running containers
echo ""
echo "📋 SDV Compatible Demo Environment Status:"
echo "========================================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(dreamkit|uda-agent)" || echo "No matching containers found"

echo ""
echo "🌐 Access Points:"
echo "=================="
echo "KUKSA Data Broker:        http://localhost:55555"
echo "Kit Server Adapter:        http://localhost:3090"
echo ""

echo "📱 SDV Compatible Demo Apps:"
echo "============================="
echo "1. Speed Monitor (SDV)  - Vehicle.Speed subscription with Velocitas SDK"
echo "2. GPS Tracker (SDV)     - GPS tracking with async patterns and MQTT"
echo ""

echo "🎯 SDV Compatible Demo Commands:"
echo "================================="
echo "# Deploy SDV speed monitoring app:"
echo "curl -X POST http://localhost:3090/api/v1/deploy \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"app_name\":\"speed-monitor\",\"type\":\"python\",\"code\":\"$(cat demo-apps/speed-monitor.py | base64 -w 0)\"}'"
echo ""
echo "# Deploy SDV GPS tracking app:"
echo "curl -X POST http://localhost:3090/api/v1/deploy \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"app_name\":\"gps-tracker\",\"type\":\"python\",\"code\":\"$(cat demo-apps/gps-tracker.py | base64 -w 0)\"}'"
echo ""

echo "🔍 SDV Signal Testing Commands:"
echo "================================="
echo "# Test Vehicle.Speed signal:"
echo "curl http://localhost:55555/vss/api/v1/signals/Vehicle.Speed"
echo ""
echo "# Test GPS signals:"
echo "curl http://localhost:55555/vss/api/v1/signals/Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Latitude"
echo "curl http://localhost:55555/vss/api/v1/signals/Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Longitude"
echo ""

echo "📊 SDV Compatible Features:"
echo "=========================="
echo "✅ Velocitas Python SDK integration"
echo "✅ VehicleApp inheritance and patterns"
echo "✅ Async/await architecture"
echo "✅ Signal subscription (vs polling)"
echo "✅ Structured logging with OpenTelemetry"
echo "✅ MQTT topic subscriptions"
echo "✅ Proper VSS signal paths"
echo "✅ Graceful error handling"
echo "✅ Production-ready patterns"
echo ""

echo "🔍 SDV Monitoring Commands:"
echo "============================"
echo "# View UDA Agent logs (SDV mode):"
echo "docker logs uda-agent-sdv-demo -f"
echo ""
echo "# View Kit Server Adapter logs:"
echo "docker logs dreamkit-kit-adapter -f"
echo ""
echo "# View KUKSA Data Broker logs:"
echo "docker logs dreamkit-sdv-runtime -f"
echo ""

echo "📊 Image Size Comparison:"
echo "========================"
echo "Ultra-lightweight UDA:    ~25MB (no Velocitas SDK)"
echo "SDV Compatible UDA:       ~50MB (with Velocitas SDK)"
echo "Full SDV Runtime:         ~500MB+"
echo ""

echo "🛑 To stop the SDV demo:"
echo "========================"
echo "docker stop uda-agent-sdv-demo dreamkit-kit-adapter dreamkit-sdv-runtime"
echo "docker rm uda-agent-sdv-demo dreamkit-kit-adapter dreamkit-sdv-runtime"
echo ""

echo "✅ SDV Runtime Compatible UDA Demo is ready! 🎉"
echo ""
echo "🚀 This demo now follows official SDV Runtime patterns!"
echo "📱 Apps use Velocitas SDK, async/await, and proper VSS integration!"