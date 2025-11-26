#!/usr/bin/env python3
"""
Test script to simulate Kit Server run_python_app message
"""

import socketio
import time
import json

def test_run_python_app():
    """Test run_python_app message to UDA agent"""

    # Create Socket.IO client
    sio = socketio.Client()

    # Simple test Python code
    test_code = '''
import time
import datetime

print("🚀 Python app started directly!")
print(f"⏰ Current time: {datetime.datetime.now()}")

for i in range(3):
    print(f"🔄 Processing step {i+1}...")
    time.sleep(1)
    print(f"✅ Step {i+1} completed!")

print("🎉 Direct execution completed!")
'''

    @sio.event
    def connect():
        print("✅ Connected to UDA agent")

        # Send run_python_app message
        run_message = {
            "cmd": "run_python_app",
            "request_from": "test-client-002",
            "to_kit_id": "Runtime-UDA-5dc4bfa4",
            "name": "test-run-app",
            "code": test_code,
            "prototype": {"name": "RunApp"}
        }

        print("📤 Sending run_python_app message...")
        sio.emit('messageToKit', run_message)

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

        # Wait for response and app execution
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    print("🧪 Testing run_python_app message to UDA agent")
    print("=" * 50)
    test_run_python_app()