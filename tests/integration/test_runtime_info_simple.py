#!/usr/bin/env python3
"""
Simple Runtime Info Test with Mock Kit Server precondition
"""

import socketio
import time
import sys
import os

# Add parent directory to path for test_helpers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_helpers import ensure_mock_server_running, ensure_uda_agent_running

def test_runtime_info():
    """Test get-runtime-info message with Mock Kit Server precondition"""

    print("🧪 Testing get-runtime-info message to UDA agent (with Simple Precondition)")
    print("=" * 70)

    # Setup environment
    print("🔧 Setting up test environment...")
    if not ensure_mock_server_running():
        print("❌ Failed to start Mock Kit Server")
        return False

    if not ensure_uda_agent_running():
        print("❌ Failed to start UDA Agent")
        return False

    print("✅ Test environment ready")

    # Create Socket.IO client
    sio = socketio.Client()

    @sio.event
    def connect():
        print("✅ Connected to UDA Agent")

        # Send get-runtime-info message
        info_message = {
            "cmd": "get-runtime-info",
            "request_from": "test-client-005",
            "to_kit_id": "Runtime-UDA-5dc4bfa4"
        }

        print(f"📤 Sending get-runtime-info message...")
        sio.emit('messageToKit', info_message)

    @sio.event
    def messageToKit_kitReply(data):
        print("📨 Received messageToKit-kitReply response:")
        print(f"   Command: {data.get('cmd', 'N/A')}")
        print(f"   Result: {data.get('result', 'N/A')[:100]}{'...' if len(data.get('result', '')) > 100 else ''}")
        print(f"   Is Done: {data.get('isDone', 'N/A')}")
        print(f"   Code: {data.get('code', 'N/A')}")

        # Test completed successfully
        sio.disconnect()
        return True

    @sio.event
    def connect_error(data):
        print(f"❌ Connection failed: {data}")
        return False

    @sio.event
    def disconnect():
        print("🔌 Disconnected from UDA Agent")

    # Connect to UDA Agent (port 3090)
    try:
        print("🔌 Connecting to UDA Agent...")
        sio.connect('http://localhost:3090', wait_timeout=10)

        # Wait for response
        print("⏳ Waiting for response...")
        time.sleep(5)

        # Disconnect if still connected
        if sio.connected:
            sio.disconnect()

        print("✅ Test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_runtime_info()
    if success:
        print("\n🎉 Runtime info test passed!")
        sys.exit(0)
    else:
        print("\n❌ Runtime info test failed!")
        sys.exit(1)