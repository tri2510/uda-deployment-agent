#!/usr/bin/env python3
"""
Test script to verify UDA agent can send output messages to Kit Server
This tests the UDA agent's ability to send logs, status updates, and other output back
"""

import socketio
import time
import json
import subprocess
import sys
import os
import signal
import atexit

def test_output_to_kitserver():
    """Test UDA agent output messages to Kit Server"""

    # Create Socket.IO client
    sio = socketio.Client()

    # Test Python code that generates output
    test_code = '''
import time
import datetime
import sys

print("🚀 UDA Agent Output Test Started!")
print(f"⏰ Current timestamp: {datetime.datetime.now().isoformat()}")

# Send multiple output messages to test message routing
for i in range(5):
    print(f"📊 Status Update {i+1}: Processing step...")
    time.sleep(1)
    print(f"✅ Step {i+1} completed successfully!")
    if i == 2:
        print("⚠️ Warning: This is a test warning message")
    if i == 4:
        print("🎉 Final step completed!")

print("📈 Test Summary: All output messages sent successfully!")
print("🏁 UDA Agent Output Test Finished!")
'''

    @sio.event
    def connect():
        print("✅ Connected to UDA agent")

        # Send run_python_app message with output-generating code
        run_message = {
            "cmd": "run_python_app",
            "request_from": "test-output-client",
            "to_kit_id": "Runtime-UDA-5dc4bfa4",
            "name": "output-test-app",
            "code": test_code,
            "prototype": {"name": "OutputTestApp"}
        }

        print("📤 Sending run_python_app message with output-generating code...")
        print("🎯 This will test UDA agent's ability to send output back to Kit Server")
        sio.emit('messageToKit', run_message)

    @sio.event
    def disconnect():
        print("❌ Disconnected from UDA agent")

    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 Received event: {event}")

        # Handle different types of messages from UDA agent
        if event == 'messageToKit':
            # This is an incoming request from test client
            if isinstance(data, dict):
                cmd = data.get('cmd', '')
                request_from = data.get('request_from', '')
                print(f"📨 Incoming request: {cmd} from {request_from}")

        elif event == 'messageToKit-kitReply':
            # This is the SDV runtime compatible response from UDA agent!
            if isinstance(data, dict):
                kit_id = data.get('kit_id', '')
                cmd = data.get('cmd', '')
                request_from = data.get('request_from', '')
                result = data.get('result', '')
                is_done = data.get('isDone', True)
                code = data.get('code', 0)
                token = data.get('token', '')

                print(f"📨 SDV Response: {cmd} (kit: {kit_id[:15]}...)")
                print(f"   Request from: {request_from}")
                print(f"   Is Done: {is_done}, Code: {code}")
                if token:
                    print(f"   Token: {token}")

                if is_done:
                    # Final response
                    if code == 0:
                        print(f"✅ Final Response: {result}")
                    else:
                        print(f"❌ Final Error: {result}")
                else:
                    # Streaming output line
                    print(f"📄 Streaming Output: {result}")

                # Display full response for debugging
                if isinstance(data, dict) and len(str(data)) < 600:
                    print(f"📦 Full Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"📦 Response: {str(result)[:150]}...")

        elif event == 'deployment_status':
            print(f"🚀 Deployment Status: {data}")
            if isinstance(data, dict):
                status = data.get('status', '')
                app_name = data.get('app_name', '')
                print(f"   App: {app_name}, Status: {status}")

        elif event == 'app_status':
            print(f"📱 App Status Update: {data}")
            if isinstance(data, dict):
                app_name = data.get('app_name', '')
                status = data.get('status', '')
                print(f"   App: {app_name}, Status: {status}")

        elif event == 'report-runtime-state':
            print(f"🖥️ Runtime State Report: {data}")
            if isinstance(data, dict):
                kit_id = data.get('kit_id', '')
                data_content = data.get('data', {})
                print(f"   Kit: {kit_id}")
                if isinstance(data_content, dict):
                    no_of_runners = data_content.get('noOfRunner', 0)
                    apps = data_content.get('apps', [])
                    print(f"   Running apps: {no_of_runners}")
                    print(f"   App list: {apps}")

        elif event in ['app_output', 'stdout', 'log_stream']:
            # These would be real-time stdout events
            print(f"📄 Real-time Output ({event}): {data}")

        else:
            # Any other potential real-time events
            if isinstance(data, dict) and len(str(data)) < 400:
                print(f"📦 {event} data: {json.dumps(data, indent=2)}")
            elif isinstance(data, str) and len(data) < 200:
                print(f"📦 {event} data: {data}")
            else:
                print(f"📦 {event}: {type(data).__name__} data received")

    try:
        print("🔌 Connecting to Mock Kit Server at http://localhost:3091...")
        sio.connect('http://localhost:3091')

        # Wait for app execution and output messages
        print("⏳ Waiting for app execution and output messages (25 seconds)...")
        print("🔍 Monitoring for: deployment_status, app_status, device_status, and real-time stdout events")
        time.sleep(25)

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
            sys.executable, 'mock_kit_server.py'
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
    print("🧪 Testing UDA Agent Output Messages to Kit Server (with Auto-Setup)")
    print("=" * 75)

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
        print("\n🧪 Running output messages test...")
        print("📝 This test will verify UDA agent's ability to send various types of output")
        print("📡 Including: status updates, log messages, execution results, and errors")
        test_output_to_kitserver()

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        # Cleanup is handled by atexit functions
        print("\n🧹 Cleanup completed!")