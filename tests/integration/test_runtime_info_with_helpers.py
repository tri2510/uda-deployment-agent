#!/usr/bin/env python3
"""
Runtime Info Test using Helper Functions
Demonstrates proper use of Mock Kit Server precondition functions
"""

import socketio
import time
import sys
import os

# Add parent directory to path for test_helpers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_helpers import setup_test_environment, teardown_test_environment

def test_runtime_info_with_helpers():
    """Test get-runtime-info message using helper functions"""

    print("🧪 Testing get-runtime-info with Helper Functions")
    print("=" * 60)

    # Setup complete test environment
    if not setup_test_environment():
        print("❌ Failed to setup test environment")
        return False

    try:
        # Create Socket.IO client
        sio = socketio.Client()

        test_results = {
            'connected': False,
            'response_received': False,
            'response_data': None
        }

        @sio.event
        def connect():
            print("✅ Connected to UDA Agent")
            test_results['connected'] = True

            # Send get-runtime-info message
            info_message = {
                "cmd": "get-runtime-info",
                "request_from": "helper-test-client",
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

            test_results['response_received'] = True
            test_results['response_data'] = data

            # Test completed successfully
            sio.disconnect()

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
            max_wait = 10
            for i in range(max_wait):
                if test_results['response_received']:
                    break
                time.sleep(1)

            # Disconnect if still connected
            if sio.connected:
                sio.disconnect()

            # Evaluate test results
            print("\n📊 Test Results:")
            print(f"   Connected to UDA Agent: {'✅' if test_results['connected'] else '❌'}")
            print(f"   Received response: {'✅' if test_results['response_received'] else '❌'}")

            if test_results['connected'] and test_results['response_received']:
                print("✅ Test completed successfully")
                return True
            else:
                print("❌ Test failed - did not receive proper response")
                return False

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False

    finally:
        # Always clean up
        teardown_test_environment()

if __name__ == "__main__":
    success = test_runtime_info_with_helpers()
    if success:
        print("\n🎉 Runtime info test with helpers passed!")
        sys.exit(0)
    else:
        print("\n❌ Runtime info test with helpers failed!")
        sys.exit(1)