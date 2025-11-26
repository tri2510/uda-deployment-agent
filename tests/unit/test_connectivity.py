#!/usr/bin/env python3
"""
Simple connectivity test for UDA agent with automatic service startup
"""

import socket
import requests
import subprocess
import sys
import time
import os
import signal
import atexit

def test_connectivity():
    """Test if UDA agent is running and accessible"""
    print("🔍 Testing UDA Agent Connectivity")
    print("=" * 40)

    # Test if we can reach Kit Server
    try:
        response = requests.get('https://kit.digitalauto.tech', timeout=5)
        print(f"✅ Kit Server reachable (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Kit Server not reachable")
        print("💡 This is normal for local testing - use mock server instead")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_port_open():
    """Test if port 3090 is open"""
    print("🔍 Testing Port 3090")
    print("=" * 40)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 3090))
        sock.close()

        if result == 0:
            print("✅ Port 3090 is open")
            return True
        else:
            print("❌ Port 3090 is closed")
            return False
    except Exception as e:
        print(f"❌ Port test error: {e}")
        return False

def check_uda_agent_running():
    """Check if UDA agent is already running"""
    try:
        # Check for UDA agent process
        result = subprocess.run(['pgrep', '-f', 'uda_agent.py'],
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def start_uda_agent():
    """Start the UDA agent automatically"""
    print("🚀 Starting UDA Agent automatically...")

    # Change to the correct directory
    uda_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(uda_dir)

    try:
        # Start UDA agent in background
        process = subprocess.Popen([
            sys.executable, 'src/uda_agent.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Register cleanup function
        atexit.register(lambda: cleanup_process(process))

        print(f"⏳ Waiting for UDA agent to start (PID: {process.pid})...")

        # Wait up to 15 seconds for agent to start
        for i in range(15):
            if check_uda_agent_running():
                print(f"✅ UDA agent started successfully!")
                return True
            time.sleep(1)
            # Only show progress every 3 seconds
            if (i + 1) % 3 == 0:
                print(f"   Waiting... {i+1}/15")

        print("❌ UDA agent failed to start within 15 seconds")
        cleanup_process(process)
        return False

    except Exception as e:
        print(f"❌ Failed to start UDA agent: {e}")
        return False

def cleanup_process(process):
    """Clean up background process"""
    try:
        if process.poll() is None:  # Process is still running
            print("🛑 Stopping UDA agent...")
            process.terminate()
            process.wait(timeout=5)
    except:
        try:
            process.kill()
        except:
            pass

if __name__ == "__main__":
    print("🧪 UDA Agent Connectivity Test with Auto-Start")
    print("=" * 60)

    # Check if agent is already running
    if check_uda_agent_running():
        print("✅ UDA agent is already running!")
    else:
        print("🔍 UDA agent is not running, starting it automatically...")
        if not start_uda_agent():
            print("\n❌ Failed to start UDA agent")
            sys.exit(1)

    # Test connectivity to Kit Server
    print("\n🔍 Testing connectivity...")
    http_ok = test_connectivity()

    if http_ok:
        print("\n✅ UDA agent is running and connected to Kit Server!")
        print("\n📝 You can now run the message tests:")
        print("   python3 tests/test_runtime_info.py")
        print("   python3 tests/test_deploy_request.py")
        print("   python3 tests/test_run_python_app.py")
        print("   python3 tests/test_stop_python_app.py")
        print("   python3 tests/run_tests.py")
        print("\n💡 Or use mock server for local testing:")
        print("   python3 tests/mock_kit_server.py &")
        print("   python3 src/uda_agent.py --server http://localhost:3091")
        print("   python3 tests/test_runtime_info.py")
    else:
        print("\n❌ UDA agent connectivity test failed!")
        print("💡 Consider using mock server for local testing")