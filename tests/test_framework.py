#!/usr/bin/env python3

"""
UDA Testing Framework
Comprehensive testing for Universal Deployment Agent
Supports Docker/Non-Docker modes with 3 devices each for complete testing
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import requests
import socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestDevice:
    """Represents a test device for UDA testing"""
    device_id: str
    device_name: str
    deployment_mode: str  # 'docker' or 'nondocker'
    process: Optional[subprocess.Popen] = None
    container_id: Optional[str] = None
    status: str = 'initialized'
    deployed_apps: List[str] = None
    logs: List[str] = None

    def __post_init__(self):
        if self.deployed_apps is None:
            self.deployed_apps = []
        if self.logs is None:
            self.logs = []

class UDATestFramework:
    """Comprehensive testing framework for UDA"""

    def __init__(self):
        self.kit_server_url = "http://localhost:3090"
        self.kuksa_url = "http://localhost:55555"
        self.devices: Dict[str, TestDevice] = {}
        self.test_results: List[Dict[str, Any]] = []
        self.current_test_id = 0

    def get_test_id(self) -> str:
        """Generate unique test ID"""
        self.current_test_id += 1
        return f"test_{self.current_test_id:03d}"

    async def setup_infrastructure(self):
        """Setup required infrastructure for testing"""
        logger.info("🚀 Setting up UDA test infrastructure...")

        # Test Kit Server Adapter connectivity
        try:
            response = requests.get(f"{self.kit_server_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Kit Server Adapter is running")
            else:
                logger.error("❌ Kit Server Adapter health check failed")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Kit Server Adapter: {e}")
            logger.info("💡 Please run: ./start-demo.sh to start infrastructure")
            return False

        # Test KUKSA Data Broker connectivity
        try:
            response = requests.get(f"{self.kuksa_url}/vss/api/v1/status", timeout=5)
            if response.status_code == 200:
                logger.info("✅ KUKSA Data Broker is running")
            else:
                logger.error("❌ KUKSA Data Broker status check failed")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to KUKSA Data Broker: {e}")
            return False

        logger.info("✅ Infrastructure setup complete")
        return True

    def create_test_devices(self, deployment_mode: str, count: int = 3) -> List[TestDevice]:
        """Create test devices for specified deployment mode"""
        logger.info(f"🔧 Creating {count} test devices for {deployment_mode} mode...")

        devices = []
        for i in range(count):
            device_id = f"test-device-{deployment_mode}-{i+1:02d}"
            device_name = f"Test Device {deployment_mode.title()} {i+1}"

            device = TestDevice(
                device_id=device_id,
                device_name=device_name,
                deployment_mode=deployment_mode,
                status='created'
            )

            devices.append(device)
            self.devices[device_id] = device
            logger.info(f"📱 Created device: {device_id}")

        return devices

    async def start_device(self, device: TestDevice) -> bool:
        """Start a test device based on deployment mode"""
        logger.info(f"🚀 Starting device: {device.device_id} ({device.deployment_mode})")

        try:
            if device.deployment_mode == 'docker':
                success = await self.start_docker_device(device)
            else:  # nondocker
                success = await self.start_nondocker_device(device)

            if success:
                device.status = 'running'
                logger.info(f"✅ Device started: {device.device_id}")
            else:
                device.status = 'failed'
                logger.error(f"❌ Device failed to start: {device.device_id}")

            return success

        except Exception as e:
            device.status = 'error'
            device.logs.append(f"Error starting device: {e}")
            logger.error(f"❌ Error starting device {device.device_id}: {e}")
            return False

    async def start_docker_device(self, device: TestDevice) -> bool:
        """Start device in Docker container"""
        try:
            # Build Docker image if not exists
            logger.info(f"🐳 Building Docker image for device: {device.device_id}")
            build_result = subprocess.run(
                ["docker", "build", "-t", f"uda-agent:{device.device_id}", "."],
                capture_output=True, text=True, cwd=Path(__file__).parent.parent
            )

            if build_result.returncode != 0:
                logger.error(f"Docker build failed: {build_result.stderr}")
                return False

            # Run container
            logger.info(f"🐳 Starting Docker container for device: {device.device_id}")
            run_result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", device.device_id,
                    "--network", "dreamkit-network",
                    "-e", f"KIT_SERVER_URL={self.kit_server_url}",
                    "-e", f"DEVICE_ID={device.device_id}",
                    f"uda-agent:{device.device_id}"
                ],
                capture_output=True, text=True
            )

            if run_result.returncode == 0:
                device.container_id = run_result.stdout.strip()
                # Wait a moment for container to start
                await asyncio.sleep(3)
                return True
            else:
                logger.error(f"Docker run failed: {run_result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error starting Docker device: {e}")
            return False

    async def start_nondocker_device(self, device: TestDevice) -> bool:
        """Start device as Python process (non-Docker)"""
        try:
            logger.info(f"🐍 Starting Python process for device: {device.device_id}")

            # Install dependencies
            logger.info(f"📦 Installing dependencies for device: {device.device_id}")
            pip_result = subprocess.run(
                ["pip3", "install", "-r", "requirements.txt"],
                capture_output=True, text=True,
                cwd=Path(__file__).parent.parent
            )

            if pip_result.returncode != 0:
                logger.error(f"Dependencies installation failed: {pip_result.stderr}")
                return False

            # Start Python process
            env = os.environ.copy()
            env.update({
                'KIT_SERVER_URL': self.kit_server_url,
                'DEVICE_ID': device.device_id,
                'PYTHONUNBUFFERED': '1'
            })

            device.process = subprocess.Popen(
                ["python3", "ultra-lightweight-uda-agent.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            # Wait for process to start
            await asyncio.sleep(2)

            # Check if process is still running
            if device.process.poll() is None:
                logger.info(f"✅ Python process started for device: {device.device_id}")
                return True
            else:
                logger.error(f"Python process exited immediately for device: {device.device_id}")
                return False

        except Exception as e:
            logger.error(f"Error starting Python device: {e}")
            return False

    def stop_device(self, device: TestDevice) -> bool:
        """Stop a test device"""
        logger.info(f"🛑 Stopping device: {device.device_id}")

        try:
            if device.deployment_mode == 'docker' and device.container_id:
                # Stop Docker container
                subprocess.run(["docker", "stop", device.container_id], capture_output=True)
                subprocess.run(["docker", "rm", device.container_id], capture_output=True)
                device.container_id = None
            elif device.deployment_mode == 'nondocker' and device.process:
                # Stop Python process
                device.process.terminate()
                try:
                    device.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    device.process.kill()
                    device.process.wait()
                device.process = None

            device.status = 'stopped'
            logger.info(f"✅ Device stopped: {device.device_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping device {device.device_id}: {e}")
            return False

    def get_device_logs(self, device: TestDevice) -> str:
        """Get logs from a device"""
        try:
            if device.deployment_mode == 'docker' and device.container_id:
                result = subprocess.run(
                    ["docker", "logs", device.container_id],
                    capture_output=True, text=True
                )
                return result.stdout
            elif device.deployment_mode == 'nondocker' and device.process:
                # For Python process, logs are in process.stdout
                if device.process.stdout:
                    device.process.stdout.seek(0)
                    return device.process.stdout.read()
                return "No logs available"
            else:
                return "Device not running"
        except Exception as e:
            return f"Error getting logs: {e}"

    async def test_device_registration(self, device: TestDevice) -> bool:
        """Test device registration with Kit Server"""
        logger.info(f"🔍 Testing device registration for: {device.device_id}")

        test_id = self.get_test_id()

        try:
            # Wait for device to connect and register
            await asyncio.sleep(5)

            # Test device connectivity via Kit Server
            response = requests.get(f"{self.kit_server_url}/api/v1/devices", timeout=10)

            if response.status_code == 200:
                devices = response.json().get('data', [])
                registered = any(d.get('device_id') == device.device_id for d in devices)

                if registered:
                    device.status = 'registered'
                    logger.info(f"✅ Device registered successfully: {device.device_id}")

                    # Record test result
                    self.test_results.append({
                        'test_id': test_id,
                        'test_name': 'device_registration',
                        'device_id': device.device_id,
                        'deployment_mode': device.deployment_mode,
                        'status': 'passed',
                        'timestamp': time.time()
                    })

                    return True
                else:
                    logger.warning(f"⚠️ Device not found in registry: {device.device_id}")
                    return False
            else:
                logger.error(f"❌ Failed to get devices from Kit Server: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error testing device registration: {e}")
            return False

    async def deploy_app_to_device(self, device: TestDevice, app_name: str, app_code: str) -> bool:
        """Deploy application to device"""
        logger.info(f"📦 Deploying app '{app_name}' to device: {device.device_id}")

        test_id = self.get_test_id()

        try:
            deployment_data = {
                'app_name': app_name,
                'device_id': device.device_id,
                'type': 'python',
                'code': app_code
            }

            response = requests.post(
                f"{self.kit_server_url}/api/v1/deploy",
                json=deployment_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    device.deployed_apps.append(app_name)
                    device.status = 'app_deployed'
                    logger.info(f"✅ App deployed successfully: {app_name} to {device.device_id}")

                    # Record test result
                    self.test_results.append({
                        'test_id': test_id,
                        'test_name': 'app_deployment',
                        'device_id': device.device_id,
                        'app_name': app_name,
                        'deployment_mode': device.deployment_mode,
                        'status': 'passed',
                        'timestamp': time.time()
                    })

                    return True
                else:
                    logger.error(f"❌ App deployment failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Deployment request failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error deploying app: {e}")
            return False

    async def test_app_execution(self, device: TestDevice, app_name: str) -> bool:
        """Test if deployed app is running properly"""
        logger.info(f"🧪 Testing app execution for: {app_name} on {device.device_id}")

        test_id = self.get_test_id()

        try:
            # Wait for app to start
            await asyncio.sleep(10)

            # Check if app signals are appearing in KUKSA
            if app_name == 'speed-monitor':
                # Check Vehicle.Speed signal
                response = requests.get(f"{self.kuksa_url}/vss/api/v1/signals/Vehicle.Speed", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Vehicle.Speed signal found - Speed Monitor app is running")

                    self.test_results.append({
                        'test_id': test_id,
                        'test_name': 'app_execution_speed_monitor',
                        'device_id': device.device_id,
                        'app_name': app_name,
                        'deployment_mode': device.deployment_mode,
                        'status': 'passed',
                        'timestamp': time.time()
                    })

                    return True
                else:
                    logger.warning(f"⚠️ Vehicle.Speed signal not found")
                    return False

            elif app_name == 'gps-tracker':
                # Check GPS signals
                lat_response = requests.get(f"{self.kuksa_url}/vss/api/v1/signals/Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Latitude", timeout=5)
                lon_response = requests.get(f"{self.kuksa_url}/vss/api/v1/signals/Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Longitude", timeout=5)

                if lat_response.status_code == 200 and lon_response.status_code == 200:
                    logger.info(f"✅ GPS signals found - GPS Tracker app is running")

                    self.test_results.append({
                        'test_id': test_id,
                        'test_name': 'app_execution_gps_tracker',
                        'device_id': device.device_id,
                        'app_name': app_name,
                        'deployment_mode': device.deployment_mode,
                        'status': 'passed',
                        'timestamp': time.time()
                    })

                    return True
                else:
                    logger.warning(f"⚠️ GPS signals not found")
                    return False

            else:
                logger.info(f"✅ Generic app execution test passed for: {app_name}")
                return True

        except Exception as e:
            logger.error(f"❌ Error testing app execution: {e}")
            return False

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        logger.info("📊 Generating test report...")

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'passed'])
        failed_tests = total_tests - passed_tests

        report = f"""
# UDA Test Report

## Test Summary
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {passed_tests/total_tests*100:.1f}%

## Test Results By Deployment Mode
"""

        # Group results by deployment mode
        modes = {}
        for result in self.test_results:
            mode = result.get('deployment_mode', 'unknown')
            if mode not in modes:
                modes[mode] = {'total': 0, 'passed': 0}
            modes[mode]['total'] += 1
            if result['status'] == 'passed':
                modes[mode]['passed'] += 1

        for mode, counts in modes.items():
            report += f"""
### {mode.title()} Mode
- Total Tests: {counts['total']}
- Passed: {counts['passed']}
- Failed: {counts['total'] - counts['passed']}
- Success Rate: {counts['passed']/counts['total']*100:.1f}%
"""

        report += f"""
## Detailed Test Results
"""

        for result in self.test_results:
            status_emoji = "✅" if result['status'] == 'passed' else "❌"
            report += f"""
{status_emoji} **{result['test_name']}** - {result['device_id']} ({result['deployment_mode']})
- App: {result.get('app_name', 'N/A')}
- Status: {result['status']}
- Timestamp: {result['timestamp']}
"""

        return report

    async def run_complete_test_suite(self) -> bool:
        """Run complete test suite with all modes and devices"""
        logger.info("🎯 Starting complete UDA test suite...")

        # Setup infrastructure
        if not await self.setup_infrastructure():
            return False

        # Test modes
        test_modes = ['docker', 'nondocker']
        test_apps = {
            'speed-monitor': None,  # Will load from file
            'gps-tracker': None     # Will load from file
        }

        # Load test app code from files
        try:
            with open('../demo-apps/speed-monitor.py', 'r') as f:
                test_apps['speed-monitor'] = f.read()
            with open('../demo-apps/gps-tracker.py', 'r') as f:
                test_apps['gps-tracker'] = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to load test apps: {e}")
            return False

        overall_success = True

        for mode in test_modes:
            logger.info(f"\n🔄 Testing {mode.title()} Mode")
            logger.info("=" * 50)

            # Create test devices
            devices = self.create_test_devices(mode, count=3)

            # Start all devices
            start_tasks = [self.start_device(device) for device in devices]
            start_results = await asyncio.gather(*start_tasks, return_exceptions=True)

            # Check which devices started successfully
            successful_devices = [device for device, result in zip(devices, start_results)
                                if result is True and not isinstance(result, Exception)]

            if len(successful_devices) == 0:
                logger.error(f"❌ No devices started successfully in {mode} mode")
                overall_success = False
                continue

            # Test each device
            for device in successful_devices:
                logger.info(f"\n🧪 Testing device: {device.device_id}")

                # Test registration
                reg_success = await self.test_device_registration(device)

                if reg_success:
                    # Deploy and test each app
                    for app_name, app_code in test_apps.items():
                        # Deploy app
                        deploy_success = await self.deploy_app_to_device(device, app_name, app_code)

                        if deploy_success:
                            # Test app execution
                            exec_success = await self.test_app_execution(device, app_name)
                            if not exec_success:
                                overall_success = False

                # Stop device
                self.stop_device(device)
                device.status = 'completed'

            logger.info(f"✅ {mode.title()} mode testing completed")

        # Generate and save test report
        report = self.generate_test_report()

        try:
            with open('test_report.md', 'w') as f:
                f.write(report)
            logger.info("📄 Test report saved to: test_report.md")
        except Exception as e:
            logger.error(f"❌ Failed to save test report: {e}")

        logger.info(f"\n🏁 Complete test suite finished")
        logger.info(f"Overall Success: {overall_success}")

        return overall_success

async def main():
    """Main test function"""
    framework = UDATestFramework()

    try:
        success = await framework.run_complete_test_suite()

        if success:
            logger.info("\n🎉 All tests completed successfully!")
            exit(0)
        else:
            logger.error("\n❌ Some tests failed!")
            exit(1)

    except KeyboardInterrupt:
        logger.info("\n🛑 Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"\n❌ Test suite error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())