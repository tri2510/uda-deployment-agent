#!/usr/bin/env python3
"""
Debug script to isolate Mock Kit Server and UDA agent communication issues
"""

import socketio
import time
import json
import subprocess
import sys
import os
import threading

def debug_mock_server():
    """Debug Mock Kit Server events directly"""
    print("🔍 DEBUG: Testing Mock Kit Server event handling...")

    sio = socketio.Client(logger=True, engineio_logger=True)

    @sio.event
    def connect():
        print("✅ DEBUG: Test client connected to Mock Kit Server")

        # Test kit registration
        reg_message = {
            'kit_id': 'debug-test-kit',
            'name': 'Debug Test Kit',
            'type': 'debug',
            'capabilities': ['debug'],
            'platform': 'debug'
        }
        print(f"📤 DEBUG: Sending kit registration...")
        sio.emit('register_kit', reg_message)

        # Test messageToKit
        time.sleep(1)
        test_message = {
            'cmd': 'debug-test',
            'request_from': 'debug-client',
            'to_kit_id': 'debug-test-kit',
            'data': 'test message'
        }
        print(f"📤 DEBUG: Sending messageToKit...")
        sio.emit('messageToKit', test_message)

        time.sleep(2)
        print("🔍 DEBUG: Test completed, disconnecting...")
        sio.disconnect()

    @sio.event
    def disconnect():
        print("❌ DEBUG: Test client disconnected")

    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 DEBUG: Event received: {event}")
        if isinstance(data, dict):
            print(f"📦 DEBUG: Data: {json.dumps(data, indent=2)}")
        else:
            print(f"📦 DEBUG: Data: {str(data)}")

    try:
        print("🔌 DEBUG: Connecting to Mock Kit Server...")
        sio.connect('http://localhost:3091')
        time.sleep(5)
    except Exception as e:
        print(f"❌ DEBUG: Connection error: {e}")

def start_mock_debug():
    """Start Mock Kit Server with debug logging"""
    print("🚀 DEBUG: Starting Mock Kit Server with logging...")

    # Start mock server with output visible
    process = subprocess.Popen([
        sys.executable, '../tools/mock_kit_server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
       universal_newlines=True, bufsize=1)

    def output_reader():
        for line in iter(process.stdout.readline, ''):
            print(f"[MOCK] {line.strip()}")

    # Start output reader thread
    reader_thread = threading.Thread(target=output_reader, daemon=True)
    reader_thread.start()

    # Wait for server to start
    time.sleep(3)

    if process.poll() is None:
        print(f"✅ DEBUG: Mock Kit Server started (PID: {process.pid})")
        return process
    else:
        print("❌ DEBUG: Mock Kit Server failed to start")
        return None

def test_uda_agent_directly():
    """Test UDA agent directly without Mock Kit Server"""
    print("🔍 DEBUG: Testing UDA agent direct Socket.IO connection...")

    sio = socketio.Client(logger=True, engineio_logger=True)

    @sio.event
    def connect():
        print("✅ DEBUG: Connected directly to UDA agent")

        # Send direct message
        message = {
            'cmd': 'get-runtime-info',
            'request_from': 'direct-debug-client',
            'to_kit_id': 'Runtime-UDA-5dc4bfa4'
        }
        print(f"📤 DEBUG: Sending direct message to UDA agent...")
        sio.emit('messageToKit', message)

    @sio.event
    def disconnect():
        print("❌ DEBUG: Disconnected from UDA agent")

    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 DEBUG: Direct event from UDA agent: {event}")
        if isinstance(data, dict):
            print(f"📦 DEBUG: Data: {json.dumps(data, indent=2)}")
        else:
            print(f"📦 DEBUG: Data: {str(data)}")

    try:
        # Try connecting directly to UDA agent if it's running
        print("🔌 DEBUG: Attempting direct connection to UDA agent...")
        sio.connect('http://localhost:3090')  # Default UDA agent port
        time.sleep(5)
        sio.disconnect()
    except Exception as e:
        print(f"❌ DEBUG: Direct connection failed: {e}")

if __name__ == "__main__":
    print("🧪 UDA Agent Communication Debug")
    print("=" * 50)

    # Test 1: Mock Kit Server event handling
    print("\n1️⃣ Testing Mock Kit Server event handling...")
    mock_process = start_mock_debug()
    if mock_process:
        try:
            debug_mock_server()
        finally:
            print("🛑 DEBUG: Stopping Mock Kit Server...")
            mock_process.terminate()
            mock_process.wait()

    # Test 2: Direct UDA agent connection
    print("\n2️⃣ Testing direct UDA agent connection...")
    test_uda_agent_directly()

    print("\n🏁 Debug completed!")