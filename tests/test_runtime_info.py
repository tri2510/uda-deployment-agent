#!/usr/bin/env python3
"""
Test script to simulate Kit Server get-runtime-info message
"""

import socketio
import time
import json

def test_runtime_info():
    """Test get-runtime-info message to UDA agent"""

    # Create Socket.IO client
    sio = socketio.Client()

    @sio.event
    def connect():
        print("✅ Connected to UDA agent")

        # Send get-runtime-info message
        info_message = {
            "cmd": "get-runtime-info",
            "request_from": "test-client-004",
            "to_kit_id": "Runtime-UDA-5dc4bfa4"
        }

        print("📤 Sending get-runtime-info message...")
        sio.emit('messageToKit', info_message)

    @sio.event
    def disconnect():
        print("❌ Disconnected from UDA agent")

    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 Received event: {event}")
        if isinstance(data, dict) and len(str(data)) < 800:
            print(f"📦 Data: {json.dumps(data, indent=2)}")
        elif isinstance(data, str) and len(data) < 300:
            print(f"📦 Data: {data}")

    try:
        print("🔌 Connecting to Mock Kit Server at http://localhost:3091...")
        sio.connect('http://localhost:3091')

        # Wait for response
        time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    print("🧪 Testing get-runtime-info message to UDA agent")
    print("=" * 50)
    test_runtime_info()