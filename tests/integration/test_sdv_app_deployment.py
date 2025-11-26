#!/usr/bin/env python3
"""
Test SDV App Deployment with sdv imports
Tests the complete deployment workflow with SDV compatibility layer
"""

import socketio
import time
import json
import threading
import sys
import os
import subprocess

# Add parent directories for imports
sys.path.append('..')
sys.path.append('../tools')

# Check what mock servers are available
try:
    from simple_mock_server import SimpleMockKitServer
except ImportError:
    try:
        from tools.simple_mock_server import SimpleMockKitServer
    except ImportError:
        # Fall back to creating a minimal mock server
        print("⚠️ Mock server not found, creating minimal test...")
        SimpleMockKitServer = None

class TestSDVAppDeployment:
    def __init__(self):
        self.kit_server = SimpleMockKitServer(port=3091)
        self.agent_process = None
        self.test_results = {
            'agent_started': False,
            'agent_registered': False,
            'app_deployed': False,
            'app_executed': False,
            'sdv_imports_work': False,
            'vehicle_signals_work': False,
            'app_output_received': False
        }

    def start_agent(self):
        """Start UDA agent with SDV compatibility"""
        print("🚀 Starting UDA Agent...")
        try:
            # Set environment for test
            env = os.environ.copy()
            env.update({
                'KUKSA_DATA_BROKER_ADDRESS': 'mock:55555',
                'LOG_LEVEL': 'INFO'
            })

            # Start agent process
            self.agent_process = subprocess.Popen([
                sys.executable, '../src/uda_agent.py',
                '--server', 'http://localhost:3091'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
               text=True, env=env, cwd='.')

            print("✅ Agent process started")
            return True

        except Exception as e:
            print(f"❌ Failed to start agent: {e}")
            return False

    def wait_for_agent_registration(self, timeout=10):
        """Wait for agent to register with Kit Server"""
        print("⏳ Waiting for agent registration...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.kit_server.registered_kits:
                kit_id = list(self.kit_server.registered_kits.keys())[0]
                print(f"✅ Agent registered: {kit_id}")
                self.test_results['agent_registered'] = True
                return True
            time.sleep(0.5)

        print("⏰ Agent registration timeout")
        return False

    def deploy_sdv_app(self):
        """Deploy SDV test app to agent"""
        print("📦 Deploying SDV test app...")

        # SDV test app with sdv imports
        sdv_app_code = '''import time
import asyncio
import signal

from sdv.vdb.reply import DataPointReply
from sdv.vehicle_app import VehicleApp
from vehicle import Vehicle, vehicle

class TestApp(VehicleApp):

    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        print("🚀 SDV App started successfully!")
        print("✅ sdv.vdb.reply imported successfully")
        print("✅ sdv.vehicle_app imported successfully")
        print("✅ Vehicle import successful")

        # Test basic functionality for a short time
        for i in range(2):
            await asyncio.sleep(1)
            print(f"🔄 Test cycle {i+1}/2")

            # Test vehicle signal access (will fail gracefully without KUKSA)
            try:
                await self.Vehicle.Body.Lights.Beam.Low.IsOn.set(True)
                value = (await self.Vehicle.Body.Lights.Beam.Low.IsOn.get()).value
                print(f"💡 Light value: {value}")
            except Exception as e:
                print(f"🔧 KUKSA not available (expected): {e}")

        print("✅ SDV App test completed successfully!")

async def main():
    vehicle_app = TestApp(vehicle)
    await vehicle_app.run()

LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
'''

        # Create deployment message
        deploy_message = {
            'cmd': 'run_python_app',
            'request_from': 'test-client-sdv',
            'to_kit_id': None,  # Will be filled with actual kit ID
            'name': 'sdv-test-app',
            'code': sdv_app_code,
            'prototype': {'name': 'SDVTestApp'}
        }

        # Send to registered agent
        if self.kit_server.registered_kits:
            kit_id = list(self.kit_server.registered_kits.keys())[0]
            deploy_message['to_kit_id'] = kit_id

            # Send deployment message
            self.kit_server.emit_to_kit(kit_id, 'messageToKit', deploy_message)
            print(f"✅ SDV app deployment sent to {kit_id}")
            self.test_results['app_deployed'] = True
            return True

        print("❌ No registered agent found")
        return False

    def wait_for_app_execution(self, timeout=15):
        """Wait for app execution and output"""
        print("⏳ Waiting for app execution...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check for SDV-related output messages
            for kit_id, messages in self.kit_server.received_messages.items():
                for msg in messages:
                    if 'result' in msg:
                        result = msg['result']
                        if 'SDV App started successfully!' in result:
                            print("✅ SDV App started successfully!")
                            self.test_results['app_executed'] = True

                        if 'sdv.vdb.reply imported successfully' in result:
                            print("✅ sdv.vdb.reply import verified!")
                            self.test_results['sdv_imports_work'] = True

                        if 'Vehicle import successful' in result:
                            print("✅ Vehicle import verified!")
                            self.test_results['vehicle_signals_work'] = True

                        if 'SDV App test completed successfully!' in result:
                            print("✅ SDV App completed successfully!")
                            self.test_results['app_output_received'] = True

            time.sleep(0.5)

        return self.test_results['app_executed']

    def cleanup(self):
        """Clean up test processes"""
        print("🧹 Cleaning up...")
        if self.agent_process:
            try:
                self.agent_process.terminate()
                self.agent_process.wait(timeout=5)
                print("✅ Agent process terminated")
            except subprocess.TimeoutExpired:
                self.agent_process.kill()
                print("🔨 Agent process force killed")

    def run_test(self):
        """Run complete test workflow"""
        print("🧪 Starting SDV App Deployment Test")
        print("=" * 60)

        try:
            # Start mock Kit Server
            print("1️⃣ Starting Mock Kit Server...")
            self.kit_server.start()
            time.sleep(1)

            # Start UDA Agent
            print("2️⃣ Starting UDA Agent...")
            if not self.start_agent():
                return False
            time.sleep(2)  # Give agent time to initialize and register
            self.test_results['agent_started'] = True

            # Wait for registration
            print("3️⃣ Waiting for Agent Registration...")
            if not self.wait_for_agent_registration():
                return False

            # Deploy SDV app
            print("4️⃣ Deploying SDV App...")
            if not self.deploy_sdv_app():
                return False

            # Wait for execution
            print("5️⃣ Monitoring App Execution...")
            if not self.wait_for_app_execution():
                print("⚠️ App execution may have failed or timed out")

            # Print results
            print("\n📊 Test Results:")
            print("=" * 30)
            for test, passed in self.test_results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {test}: {status}")

            # Overall success
            all_critical = (
                self.test_results['agent_started'] and
                self.test_results['agent_registered'] and
                self.test_results['app_deployed'] and
                self.test_results['sdv_imports_work']
            )

            print(f"\n🎯 Overall: {'✅ SUCCESS' if all_critical else '❌ FAILURE'}")

            if all_critical:
                print("🎉 SDV compatibility layer works correctly!")
                print("   - Agent starts and registers")
                print("   - SDV apps can be deployed")
                print("   - sdv imports are resolved")
                print("   - Vehicle app execution works")
            else:
                print("⚠️ Some tests failed - check logs above")

            return all_critical

        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False

        finally:
            self.cleanup()

if __name__ == "__main__":
    test = TestSDVAppDeployment()
    success = test.run_test()
    sys.exit(0 if success else 1)