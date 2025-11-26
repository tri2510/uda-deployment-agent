#!/usr/bin/env python3
"""
Test Helper Functions
Common functions used by UDA agent tests
"""

import subprocess
import time
import socket
import sys
import os
import atexit
import psutil

class MockKitServerManager:
    """Manages Mock Kit Server lifecycle for tests"""

    def __init__(self):
        self.process = None
        self.port = 3091

    def is_running(self):
        """Check if Mock Kit Server is running on the expected port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except:
            return False

    def start(self, timeout=15):
        """Start Mock Kit Server if not already running"""
        if self.is_running():
            print("✅ Mock Kit Server is already running")
            return True

        print("🚀 Starting Mock Kit Server...")

        # Get absolute path to mock server
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mock_server_path = os.path.join(current_dir, 'tools', 'mock_kit_server.py')

        try:
            # Start mock server in background
            self.process = subprocess.Popen([
                sys.executable, mock_server_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(f"⏳ Waiting for Mock Kit Server to start (PID: {self.process.pid})...")

            # Wait for server to start
            for i in range(timeout):
                if self.is_running():
                    print(f"✅ Mock Kit Server started successfully!")

                    # Register cleanup function
                    atexit.register(self.stop)
                    return True

                time.sleep(1)
                if (i + 1) % 3 == 0:
                    print(f"   Waiting... {i+1}/{timeout}")

            print("❌ Mock Kit Server failed to start")
            self.stop()
            return False

        except Exception as e:
            print(f"❌ Failed to start Mock Kit Server: {e}")
            return False

    def stop(self):
        """Stop Mock Kit Server"""
        if self.process:
            try:
                print("🛑 Stopping Mock Kit Server...")
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✅ Mock Kit Server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing Mock Kit Server...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️  Error stopping Mock Kit Server: {e}")
            finally:
                self.process = None

        # Also kill any remaining processes using the port
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == self.port:
                            print(f"🔪 Killing process {proc.info['pid']} using port {self.port}")
                            proc.kill()
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except:
            pass

class UDAgentManager:
    """Manages UDA Agent lifecycle for tests"""

    def __init__(self, server_url="http://localhost:3091"):
        self.process = None
        self.server_url = server_url

    def is_running(self):
        """Check if UDA Agent is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 3090))  # UDA Agent default port
            sock.close()
            return result == 0
        except:
            return False

    def start(self, timeout=15):
        """Start UDA Agent if not already running"""
        if self.is_running():
            print("✅ UDA Agent is already running")
            return True

        print("🚀 Starting UDA Agent...")

        # Change to the UDA directory (parent of tests)
        uda_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        try:
            # Start UDA agent in background pointing to mock server
            self.process = subprocess.Popen([
                sys.executable, 'src/uda_agent.py', '--server', self.server_url
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=uda_dir)

            print(f"⏳ Waiting for UDA Agent to start (PID: {self.process.pid})...")

            # Wait for agent to start
            for i in range(timeout):
                if self.is_running():
                    print(f"✅ UDA Agent started successfully!")

                    # Register cleanup function
                    atexit.register(self.stop)
                    return True

                time.sleep(1)
                if (i + 1) % 3 == 0:
                    print(f"   Waiting... {i+1}/{timeout}")

            print("❌ UDA Agent failed to start within timeout")
            self.stop()
            return False

        except Exception as e:
            print(f"❌ Failed to start UDA Agent: {e}")
            return False

    def stop(self):
        """Stop UDA Agent"""
        if self.process:
            try:
                print("🛑 Stopping UDA Agent...")
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✅ UDA Agent stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing UDA Agent...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️  Error stopping UDA Agent: {e}")
            finally:
                self.process = None

def ensure_mock_server_running():
    """Ensure Mock Kit Server is running - global precondition function"""
    manager = MockKitServerManager()
    return manager.start()

def ensure_uda_agent_running(server_url="http://localhost:3091"):
    """Ensure UDA Agent is running - global precondition function"""
    manager = UDAgentManager(server_url)
    return manager.start()

def setup_test_environment():
    """Complete test environment setup"""
    print("🔧 Setting up test environment...")

    # Clean first
    try:
        import subprocess
        subprocess.run([sys.executable, 'cleanup.py'],
                      capture_output=True, text=True, timeout=60)
    except:
        pass

    # Start Mock Kit Server
    mock_success = ensure_mock_server_running()
    if not mock_success:
        print("❌ Failed to start Mock Kit Server")
        return False

    # Start UDA Agent
    uda_success = ensure_uda_agent_running()
    if not uda_success:
        print("❌ Failed to start UDA Agent")
        return False

    return True

def teardown_test_environment():
    """Clean test environment"""
    print("🧹 Tearing down test environment...")

    # Stop any running servers
    try:
        uda = UDAgentManager()
        uda.stop()
    except:
        pass

    try:
        mock = MockKitServerManager()
        mock.stop()
    except:
        pass

    print("✅ Test environment cleaned up")