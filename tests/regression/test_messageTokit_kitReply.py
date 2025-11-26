#!/usr/bin/env python3
"""
Comprehensive test to verify UDA agent emits correct messageToKit-kitReply events
"""

import socketio
import time
import json
import subprocess
import sys
import os
import signal
import atexit
import threading

def test_comprehensive_messaging():
    """Test complete messageToKit-kitReply flow"""

    # Create Socket.IO client for testing
    sio = socketio.Client()

    # Track received events
    received_events = []

    @sio.event
    def connect():
        print("✅ Test client connected to Mock Kit Server")

        # Wait a moment for UDA agent to be ready
        time.sleep(2)

        # Send runtime info request
        message = {
            'cmd': 'get-runtime-info',
            'request_from': 'comprehensive-test-client',
            'to_kit_id': 'Runtime-UDA-5dc4bfa4'
        }
        print(f"📤 Sending get-runtime-info request: {json.dumps(message, indent=2)}")
        sio.emit('messageToKit', message)
        print("🔍 Waiting for messageToKit-kitReply response...")

    @sio.event
    def disconnect():
        print("❌ Test client disconnected")

    @sio.on('*')
    def catch_all(event, data):
        timestamp = time.strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 📨 EVENT RECEIVED: {event}")

        received_events.append({
            'event': event,
            'data': data,
            'timestamp': timestamp
        })

        if isinstance(data, dict):
            if len(str(data)) < 600:
                print(f"📦 Data: {json.dumps(data, indent=2)}")
            else:
                print(f"📦 Data (keys): {list(data.keys())}")
                if 'result' in data:
                    result = str(data['result'])[:200] + ('...' if len(str(data['result'])) > 200 else '')
                    print(f"📦 Result: {result}")
        else:
            print(f"📦 Data: {str(data)[:300]}...")

        # Check specifically for our target events
        if event == 'messageToKit-kitReply':
            print(f"🎯 SUCCESS: Received messageToKit-kitReply event!")
            kit_id = data.get('kit_id', '') if isinstance(data, dict) else ''
            cmd = data.get('cmd', '') if isinstance(data, dict) else ''
            is_done = data.get('isDone', False) if isinstance(data, dict) else False
            print(f"   Kit ID: {kit_id}")
            print(f"   Command: {cmd}")
            print(f"   Is Done: {is_done}")

        elif event == 'messageToKit':
            if isinstance(data, dict):
                cmd = data.get('cmd', '')
                request_from = data.get('request_from', '')
                result = data.get('result', '')
                if result:  # This is a response
                    print(f"🔄 Received messageToKit response: {cmd}")
                    print(f"   From: {request_from}")
                    print(f"   Result: {result[:100]}{'...' if len(result) > 100 else ''}")
                else:  # This is a request
                    print(f"📤 Received messageToKit request: {cmd}")
                    print(f"   From: {request_from}")

    try:
        print("🔌 Connecting to Mock Kit Server at http://localhost:3091...")
        sio.connect('http://localhost:3091')

        # Wait for responses
        print("⏳ Waiting for events (15 seconds)...")
        time.sleep(15)

        # Analyze results
        print(f"\n📊 ANALYSIS:")
        print(f"   Total events received: {len(received_events)}")

        messageToKit_events = [e for e in received_events if e['event'] == 'messageToKit']
        messageToKit_kitReply_events = [e for e in received_events if e['event'] == 'messageToKit-kitReply']

        print(f"   messageToKit events: {len(messageToKit_events)}")
        print(f"   messageToKit-kitReply events: {len(messageToKit_kitReply_events)}")

        if messageToKit_kitReply_events:
            print(f"✅ SUCCESS: UDA agent is emitting messageToKit-kitReply events!")
            for event in messageToKit_kitReply_events:
                data = event['data']
                if isinstance(data, dict):
                    print(f"   - Command: {data.get('cmd', 'unknown')}")
                    print(f"     Kit ID: {data.get('kit_id', 'unknown')}")
                    print(f"     Is Done: {data.get('isDone', False)}")
        else:
            print(f"❌ ISSUE: UDA agent is NOT emitting messageToKit-kitReply events")
            if messageToKit_events:
                print(f"   UDA agent is using messageToKit instead of messageToKit-kitReply")

        if received_events:
            print(f"\n📝 Event Timeline:")
            for i, event in enumerate(received_events):
                print(f"   {i+1}. [{event['timestamp']}] {event['event']}")

    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

def start_mock_server():
    """Start mock Kit Server"""
    print("🚀 Starting Mock Kit Server...")

    # Use absolute path to mock_kit_server.py
    mock_server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'mock_kit_server.py')
    process = subprocess.Popen([
        sys.executable, mock_server_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
       universal_newlines=True, cwd='.')

    atexit.register(lambda: cleanup_process(process, "Mock Kit Server"))

    # Wait for server to start
    time.sleep(3)

    # Check if server started successfully
    if process.poll() is None:
        print(f"✅ Mock Kit Server started (PID: {process.pid})")
        return process
    else:
        print("❌ Mock Kit Server failed to start")
        return None

def start_uda_agent():
    """Start UDA Agent"""
    print("🚀 Starting UDA Agent...")

    # Change to parent directory
    os.chdir('..')

    process = subprocess.Popen([
        sys.executable, 'src/uda_agent.py', '--server', 'http://localhost:3091'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
       universal_newlines=True)

    atexit.register(lambda: cleanup_process(process, "UDA Agent"))

    # Change back to tests directory
    os.chdir('tests')

    # Wait for agent to start and connect
    print(f"⏳ Waiting for UDA Agent to start and connect (PID: {process.pid})...")
    time.sleep(5)

    # Check if agent started successfully
    if process.poll() is None:
        print(f"✅ UDA Agent started successfully")
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

def monitor_processes(mock_process, uda_process):
    """Monitor background processes and output their logs"""
    def monitor():
        while mock_process and mock_process.poll() is None:
            try:
                line = mock_process.stdout.readline()
                if line:
                    print(f"[MOCK] {line.strip()}")
            except:
                break

        while uda_process and uda_process.poll() is None:
            try:
                line = uda_process.stdout.readline()
                if line:
                    print(f"[UDA] {line.strip()}")
            except:
                break

    # Start monitoring in background thread
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()

    return monitor_thread

if __name__ == "__main__":
    print("🧪 Comprehensive messageToKit-kitReply Test")
    print("=" * 60)
    print("🎯 This test verifies that the UDA agent emits correct SDV-runtime")
    print("   compatible messageToKit-kitReply events instead of messageToKit")
    print("=" * 60)

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

        # Start monitoring processes (optional, can be noisy)
        # monitor_thread = monitor_processes(mock_process, uda_process)

        # Run the comprehensive test
        print("\n🧪 Starting comprehensive messaging test...")
        test_comprehensive_messaging()

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        print("\n🧹 Cleaning up...")
        # Cleanup handled by atexit functions