#!/usr/bin/env python3

"""
Isolated UDA Test Runner
Uses Mock Kit Server for complete testing without external dependencies
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
import requests

class IsolatedUDATester:
    """Isolated UDA testing with mock Kit Server"""

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

        # Test configuration
        self.mock_kit_server_url = "http://localhost:3090"
        self.mock_kit_process = None
        self.uda_processes: Dict[str, subprocess.Popen] = {}

        # Test results
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'devices': {},
            'deployments': [],
            'results': []
        }

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    async def start_mock_kit_server(self):
        """Start the mock Kit Server"""
        self.logger.info("🧪 Starting Mock Kit Server...")

        # Kill any existing process on port 3090
        try:
            subprocess.run(['pkill', '-f', 'mock_kit_server.py'], capture_output=True)
            time.sleep(1)
        except:
            pass

        # Start mock Kit Server in background
        self.mock_kit_process = subprocess.Popen([
            sys.executable, 'tests/mock_kit_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get(f"{self.mock_kit_server_url}/health", timeout=2)
                if response.status_code == 200:
                    self.logger.info("✅ Mock Kit Server started successfully")
                    return True
            except:
                pass
            await asyncio.sleep(1)

        self.logger.error("❌ Failed to start Mock Kit Server")
        return False

    async def stop_mock_kit_server(self):
        """Stop the mock Kit Server"""
        if self.mock_kit_process:
            self.logger.info("🛑 Stopping Mock Kit Server...")
            self.mock_kit_process.terminate()
            self.mock_kit_process.wait(timeout=5)

            # Clean up any remaining processes
            subprocess.run(['pkill', '-f', 'mock_kit_server.py'], capture_output=True)

    async def test_uda_agent(self, device_id: str, mode: str = 'non-docker') -> bool:
        """Test a single UDA agent"""
        self.logger.info(f"📱 Starting UDA agent {device_id} in {mode} mode...")

        try:
            # Start UDA agent with mock Kit Server
            env = os.environ.copy()
            env['KIT_SERVER_URL'] = self.mock_kit_server_url
            env['DEVICE_ID'] = device_id
            env['KUKSA_URL'] = 'http://localhost:55555'  # Even if not running, won't crash

            process = subprocess.Popen([
                sys.executable, 'ultra-lightweight-uda-agent.py'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.uda_processes[device_id] = process

            # Wait for agent to connect and register
            await asyncio.sleep(5)

            # Check if agent is still running
            if process.poll() is None:
                self.logger.info(f"✅ UDA agent {device_id} started successfully")
                self.test_results['devices'][device_id] = {
                    'id': device_id,
                    'mode': mode,
                    'status': 'running',
                    'pid': process.pid,
                    'started_at': datetime.now().isoformat()
                }
                return True
            else:
                # Agent exited, check why
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ UDA agent {device_id} failed: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to start UDA agent {device_id}: {e}")
            return False

    async def deploy_app_to_device(self, device_id: str, app_name: str) -> bool:
        """Deploy an app to a specific device via REST API"""
        self.logger.info(f"📦 Deploying {app_name} to {device_id}...")

        app_configs = {
            'speed-monitor': {
                'app_name': app_name,
                'type': 'python',
                'code': '''
import time
import json
print(f"🚀 Speed Monitor App started on device: ''' + device_id + '''")
for i in range(10):
    speed = 50 + i
    print(f"📊 Speed: {speed} km/h")
    time.sleep(1)
print("✅ Speed Monitor App completed successfully")
''',
                'execution_mode': 'background'
            },
            'gps-tracker': {
                'app_name': app_name,
                'type': 'python',
                'code': '''
import time
import json
print(f"🗺️ GPS Tracker App started on device: ''' + device_id + '''")
coords = [(52.5200, 13.4050), (52.5201, 13.4051), (52.5202, 13.4052)]
for lat, lon in coords:
    print(f"📍 Location: {lat}, {lon}")
    time.sleep(1)
print("✅ GPS Tracker App completed successfully")
''',
                'execution_mode': 'background'
            }
        }

        app_config = app_configs.get(app_name, app_configs['speed-monitor'])

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mock_kit_server_url}/api/v1/apps/deploy",
                    json={
                        'device_id': device_id,
                        'app': app_config
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"✅ App {app_name} deployed to {device_id}")

                        self.test_results['deployments'].append({
                            'device_id': device_id,
                            'app_name': app_name,
                            'app_id': result.get('app_id', app_name),
                            'deployed_at': datetime.now().isoformat(),
                            'status': 'deployed'
                        })
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Failed to deploy app: {error_text}")
                        return False

        except Exception as e:
            self.logger.error(f"❌ Error deploying app {app_name} to {device_id}: {e}")
            return False

    async def get_test_summary(self) -> dict:
        """Get comprehensive test results"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mock_kit_server_url}/api/v1/test/results") as response:
                    if response.status == 200:
                        results = await response.json()
                        return results
        except Exception as e:
            self.logger.error(f"Error getting test results: {e}")

        return {
            'test_results': [],
            'devices': {},
            'deployments': {},
            'summary': {'total_tests': 0}
        }

    async def cleanup_resources(self):
        """Clean up all test resources"""
        self.logger.info("🧹 Cleaning up test resources...")

        # Stop all UDA agents
        for device_id, process in self.uda_processes.items():
            try:
                self.logger.info(f"🛑 Stopping UDA agent {device_id}...")
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                self.logger.error(f"Error stopping agent {device_id}: {e}")
                process.kill()

        # Stop mock Kit Server
        await self.stop_mock_kit_server()

    async def run_complete_test(self):
        """Run complete isolated test suite"""
        self.logger.info("🎯 Starting Complete Isolated UDA Test Suite")

        try:
            # 1. Start Mock Kit Server
            if not await self.start_mock_kit_server():
                return False

            # 2. Test Non-Docker Mode - 3 devices
            self.logger.info("🐍 Testing Non-Docker Mode with 3 devices...")
            non_docker_devices = ['device-1', 'device-2', 'device-3']

            for device_id in non_docker_devices:
                success = await self.test_uda_agent(device_id, 'non-docker')
                if not success:
                    self.logger.error(f"Failed to start {device_id}")
                    continue

                # Deploy speed-monitor app
                await self.deploy_app_to_device(device_id, 'speed-monitor')

                # Deploy gps-tracker app
                await self.deploy_app_to_device(device_id, 'gps-tracker')

                await asyncio.sleep(2)  # Brief pause between devices

            # 3. Wait for apps to complete
            self.logger.info("⏳ Waiting for apps to complete...")
            await asyncio.sleep(10)

            # 4. Get test results
            self.logger.info("📊 Collecting test results...")
            final_results = await self.get_test_summary()

            # 5. Print comprehensive summary
            self.print_test_summary(final_results)

            self.test_results['end_time'] = datetime.now().isoformat()
            self.test_results['final_results'] = final_results

            return True

        except Exception as e:
            self.logger.error(f"❌ Test suite failed: {e}")
            return False

        finally:
            await self.cleanup_resources()

    def print_test_summary(self, results: dict):
        """Print comprehensive test summary"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📋 ISOLATED UDA TEST RESULTS")
        self.logger.info("="*60)

        summary = results.get('summary', {})
        devices = results.get('devices', {})
        deployments = results.get('deployments', {})
        test_results = results.get('test_results', [])

        self.logger.info(f"📊 Summary:")
        self.logger.info(f"   Total Tests: {summary.get('total_tests', 0)}")
        self.logger.info(f"   Devices Registered: {summary.get('devices_registered', 0)}")
        self.logger.info(f"   Apps Deployed: {summary.get('apps_deployed', 0)}")

        self.logger.info(f"\n📱 Devices ({len(devices)}):")
        for device_id, device_info in devices.items():
            status = device_info.get('status', 'unknown')
            self.logger.info(f"   ✅ {device_id}: {status}")

        self.logger.info(f"\n📦 App Deployments:")
        for device_id, apps in deployments.items():
            self.logger.info(f"   Device {device_id}:")
            for app in apps:
                app_name = app.get('app_id', 'unknown')
                status = app.get('status', 'unknown')
                self.logger.info(f"      📦 {app_name}: {status}")

        self.logger.info(f"\n🎯 Test Events ({len(test_results)}):")
        for result in test_results:
            device = result.get('device_id', 'unknown')
            app = result.get('app_id', 'unknown')
            status = result.get('status', 'unknown')
            timestamp = result.get('timestamp', 'unknown')
            self.logger.info(f"   {timestamp}: {device} - {app} - {status}")

        # Success criteria
        success = (
            summary.get('devices_registered', 0) >= 3 and
            summary.get('apps_deployed', 0) >= 6  # 2 apps per device
        )

        if success:
            self.logger.info("\n🎉 TEST SUITE PASSED!")
            self.logger.info("   ✅ 3 devices registered and connected")
            self.logger.info("   ✅ 6 apps deployed successfully (2 per device)")
            self.logger.info("   ✅ UDA communication working")
            self.logger.info("   ✅ Mock Kit Server functioning")
        else:
            self.logger.info("\n❌ TEST SUITE FAILED!")
            self.logger.info("   Review results above for issues")

        self.logger.info("="*60)

async def main():
    """Main function"""
    tester = IsolatedUDATester()

    def signal_handler(signum, frame):
        print("\n🛑 Interrupted - cleaning up...")
        asyncio.create_task(tester.cleanup_resources())
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    success = await tester.run_complete_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())