#!/usr/bin/env python3
"""
Test script to simulate Kit Server deploy_request message
"""

import socketio
import time
import json

def test_deploy_request():
    """Test deploy_request message to UDA agent"""

    # Create Socket.IO client
    sio = socketio.Client()

    # Test Python code to deploy
    test_code = '''
import time
import asyncio

print("🚀 Test app started!")

for i in range(5):
    print(f"📋 Running... iteration {i+1}/5")
    time.sleep(2)

print("✅ Test app completed successfully!")
'''

    @sio.event
    def connect():
        print("✅ Connected to UDA agent")

        # Send deploy_request message
        deploy_message = {
            "cmd": "deploy_request",
            "request_from": "test-client-001",
            "to_kit_id": "Runtime-UDA-5dc4bfa4",
            "name": "test-deploy-app",
            "code": test_code,
            "prototype": {"name": "TestApp"}
        }

        print("📤 Sending deploy_request message...")
        sio.emit('messageToKit', deploy_message)

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
        time.sleep(10)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    print("🧪 Testing deploy_request message to UDA agent")
    print("=" * 50)
    test_deploy_request()