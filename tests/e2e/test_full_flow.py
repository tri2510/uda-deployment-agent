#!/usr/bin/env python3
"""
Test full flow with Mock Kit Server and UDA Agent both running
"""

import socketio
import time
import json
import subprocess
import sys
import os
import threading
import atexit

def test_full_flow():
    """Test complete flow: Mock Server -> UDA Agent -> Mock Server -> Test Client"""

    # Create Socket.IO client for testing
    sio = socketio.Client()

    @sio.event
    def connect():
        print("✅ Test client connected to Mock Kit Server")

    @sio.event
    def disconnect():
        print("❌ Test client disconnected")

    @sio.on('*')
    def catch_all(event, data):
        print(f"\n📨 EVENT RECEIVED: {event}")
        if isinstance(data, dict):
            print(f"📦 Data: {json.dumps(data, indent=2)}")
        else:
            print(f"📦 Data: {str(data)}")

        if event == 'messageToKit-kitReply':
            print(f"🎯 SUCCESS: Received messageToKit-kitReply!")
        elif event == 'messageToKit' and isinstance(data, dict) and 'result' in data:
            print(f"🔄 INFO: Received messageToKit response: {data.get('cmd', 'unknown')}")

    try:
        print("🔌 Connecting to Mock Kit Server at http://localhost:3091...")
        sio.connect('http://localhost:3091')

        # Wait for UDA agent to connect (5 seconds)
        print("⏳ Waiting for UDA agent to connect...")
        time.sleep(5)

        # Send runtime info request
        message = {
            'cmd': 'get-runtime-info',
            'request_from': 'full-flow-test',
            'to_kit_id': 'Runtime-UDA-5dc4bfa4'
        }
        print(f"\n📤 Sending get-runtime-info request:")
        print(f"   {json.dumps(message, indent=2)}")
        sio.emit('messageToKit', message)

        # Wait for response
        print("⏳ Waiting for response (10 seconds)...")
        time.sleep(10)

    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

def start_mock_server():
    """Start Mock Kit Server with logging"""
    print("🚀 Starting Mock Kit Server...")

    mock_server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'mock_kit_server.py')
    process = subprocess.Popen([
        sys.executable, mock_server_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
       universal_newlines=True)

    def log_output():
        for line in iter(process.stdout.readline, ''):
            print(f"[MOCK] {line.strip()}")

    thread = threading.Thread(target=log_output, daemon=True)
    thread.start()

    atexit.register(lambda: cleanup_process(process, "Mock Kit Server"))

    time.sleep(3)

    if process.poll() is None:
        print(f"✅ Mock Kit Server started (PID: {process.pid})")
        return process
    else:
        print("❌ Mock Kit Server failed to start")
        return None

def start_uda_agent():
    """Start UDA Agent with logging"""
    print("🚀 Starting UDA Agent...")

    os.chdir('..')
    process = subprocess.Popen([
        sys.executable, 'src/uda_agent.py', '--server', 'http://localhost:3091'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
       universal_newlines=True)
    os.chdir('tests')

    def log_output():
        for line in iter(process.stdout.readline, ''):
            print(f"[UDA] {line.strip()}")

    thread = threading.Thread(target=log_output, daemon=True)
    thread.start()

    atexit.register(lambda: cleanup_process(process, "UDA Agent"))

    time.sleep(5)  # Give UDA agent time to connect to Mock Kit Server

    if process.poll() is None:
        print(f"✅ UDA Agent started (PID: {process.pid})")
        return process
    else:
        print("❌ UDA Agent failed to start")
        return None

def cleanup_process(process, name):
    """Clean up background process"""
    try:
        if process.poll() is None:
            print(f"🛑 Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    except:
        pass

if __name__ == "__main__":
    print("🧪 Full Flow Test: Mock Kit Server + UDA Agent + Test Client")
    print("=" * 65)

    mock_process = None
    uda_process = None

    try:
        # Start Mock Kit Server
        mock_process = start_mock_server()
        if not mock_process:
            sys.exit(1)

        # Start UDA Agent
        uda_process = start_uda_agent()
        if not uda_process:
            sys.exit(1)

        # Run the full flow test
        print("\n🧪 Running full flow test...")
        test_full_flow()

        print("\n🏁 Full flow test completed!")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        print("\n🧹 Cleanup completed!")
        # Cleanup handled by atexit functions