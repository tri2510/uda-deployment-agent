#!/usr/bin/env python3
"""
Test script to simulate Kit Server run_python_app message with auto-service startup
"""

import socketio
import time
import json
import subprocess
import sys
import os
import signal
import atexit

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
        print("🔌 Connecting to Mock Kit Server at http://localhost:3091...")
        sio.connect('http://localhost:3091')

        # Wait for response and app execution
        time.sleep(15)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

def check_mock_server_running():
    """Check if mock Kit Server is running on port 3091"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 3091))
        sock.close()
        return result == 0
    except:
        return False

def check_uda_agent_running():
    """Check if UDA agent process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'uda_agent.py.*localhost:3091'],
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def start_mock_server():
    """Start mock Kit Server"""
    print("🚀 Starting Mock Kit Server automatically...")

    # Change to tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(tests_dir)

    try:
        # Start mock server in background
        process = subprocess.Popen([
            sys.executable, '../tools/mock_kit_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Register cleanup function
        atexit.register(lambda: cleanup_process(process, "Mock Kit Server"))

        print(f"⏳ Waiting for Mock Kit Server to start (PID: {process.pid})...")

        # Wait up to 10 seconds for server to start
        for i in range(10):
            if check_mock_server_running():
                print(f"✅ Mock Kit Server started successfully!")
                return process
            time.sleep(1)
            if (i + 1) % 3 == 0:
                print(f"   Waiting... {i+1}/10")

        print("❌ Mock Kit Server failed to start within 10 seconds")
        cleanup_process(process, "Mock Kit Server")
        return None

    except Exception as e:
        print(f"❌ Failed to start Mock Kit Server: {e}")
        return None

def start_uda_agent():
    """Start UDA agent pointing to mock server"""
    print("🚀 Starting UDA Agent with mock server...")

    # Change to the UDA directory
    uda_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(uda_dir)

    try:
        # Start UDA agent in background pointing to mock server
        process = subprocess.Popen([
            sys.executable, 'src/uda_agent.py', '--server', 'http://localhost:3091'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Register cleanup function
        atexit.register(lambda: cleanup_process(process, "UDA Agent"))

        print(f"⏳ Waiting for UDA Agent to start (PID: {process.pid})...")

        # Wait up to 10 seconds for agent to start
        for i in range(10):
            if check_uda_agent_running():
                print(f"✅ UDA Agent started successfully!")
                return process
            time.sleep(1)
            if (i + 1) % 3 == 0:
                print(f"   Waiting... {i+1}/10")

        print("❌ UDA Agent failed to start within 10 seconds")
        cleanup_process(process, "UDA Agent")
        return None

    except Exception as e:
        print(f"❌ Failed to start UDA Agent: {e}")
        return None

def cleanup_process(process, name):
    """Clean up background process"""
    try:
        if process.poll() is None:  # Process is still running
            print(f"🛑 Stopping {name}...")
            process.terminate()
            process.wait(timeout=5)
    except:
        try:
            process.kill()
        except:
            pass

if __name__ == "__main__":
    print("🧪 Testing run_python_app message to UDA agent (with Auto-Setup)")
    print("=" * 70)

    mock_process = None
    uda_process = None

    try:
        # Check if mock server is running
        if not check_mock_server_running():
            mock_process = start_mock_server()
            if not mock_process:
                print("❌ Failed to start Mock Kit Server")
                sys.exit(1)
        else:
            print("✅ Mock Kit Server is already running!")

        # Check if UDA agent is running
        if not check_uda_agent_running():
            uda_process = start_uda_agent()
            if not uda_process:
                print("❌ Failed to start UDA Agent")
                sys.exit(1)
        else:
            print("✅ UDA Agent is already running!")

        # Wait a moment for everything to be ready
        time.sleep(2)

        # Run the test
        print("\n🧪 Running run_python_app test...")
        test_run_python_app()

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        # Cleanup is handled by atexit functions
        print("\n🧹 Cleanup completed!")