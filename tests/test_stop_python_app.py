#!/usr/bin/env python3
"""
Test script to simulate Kit Server stop_python_app message
"""

import socketio
import time
import json

def test_stop_python_app():
    """Test stop_python_app message to UDA agent"""

    # Create Socket.IO client
    sio = socketio.Client()

    @sio.event
    def connect():
        print("✅ Connected to UDA agent")

        # Send stop_python_app message for a running app
        stop_message = {
            "cmd": "stop_python_app",
            "request_from": "test-client-003",
            "to_kit_id": "Runtime-UDA-5dc4bfa4",
            "name": "test-deploy-app"  # Assuming this app is running from previous test
        }

        print("📤 Sending stop_python_app message...")
        print("🎯 Target app: test-deploy-app")
        sio.emit('messageToKit', stop_message)

    @sio.event
    def disconnect():
        print("❌ Disconnected from UDA agent")

    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 Received event: {event}")
        if isinstance(data, dict) and len(str(data)) < 500:
            print(f"📦 Data: {json.dumps(data, indent=2)}")
        elif isinstance(data, str) and len(data) < 200:
            print(f"📦 Data: {data}")

    try:
        print("🔌 Connecting to UDA agent at http://localhost:3090...")
        sio.connect('http://localhost:3090')

        # Wait for response
        time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    print("🧪 Testing stop_python_app message to UDA agent")
    print("=" * 50)
    print("⚠️  Make sure 'test-deploy-app' is running from previous test!")
    print()
    test_stop_python_app()