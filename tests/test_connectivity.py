#!/usr/bin/env python3
"""
Simple connectivity test for UDA agent
"""

import socket
import requests

def test_connectivity():
    """Test if UDA agent is running and accessible"""
    print("🔍 Testing UDA Agent Connectivity")
    print("=" * 40)

    # Test HTTP connectivity
    try:
        response = requests.get('http://localhost:3090', timeout=5)
        print(f"✅ HTTP connection successful (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ HTTP connection failed - UDA agent not running on localhost:3090")
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

if __name__ == "__main__":
    print("🧪 UDA Agent Connectivity Test")
    print("=" * 50)

    port_open = test_port_open()
    print()
    http_ok = test_connectivity()

    if port_open and http_ok:
        print("\n✅ UDA agent is running and accessible!")
        print("\n📝 You can now run the message tests:")
        print("   python3 tests/test_runtime_info.py")
        print("   python3 tests/test_deploy_request.py")
        print("   python3 tests/test_run_python_app.py")
        print("   python3 tests/test_stop_python_app.py")
        print("   python3 tests/run_tests.py")
    else:
        print("\n❌ UDA agent is not running!")
        print("\n🚀 To start the UDA agent:")
        print("   cd /home/htr1hc/01_SDV/73_autowrx_v3/autowrx-sdv-rnd/uda-agent")
        print("   python3 src/uda_agent.py")
        print("\nThe agent should connect to https://kit.digitalauto.tech")
        print("and listen for Kit Server messages on localhost:3090")