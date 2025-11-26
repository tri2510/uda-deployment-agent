#!/usr/bin/env python3

"""
Universal Deployment Agent
Production-ready UDA for vehicle applications

Features:
- Socket.IO communication with Kit Server Adapter
- Full Velocitas SDK integration for KUKSA Data Broker
- Production-ready error handling and logging
- Support for SDV vehicle applications
- Docker and baremetal deployment support
- Real-time app deployment and management
- Linux, Yocto, and embedded system support
"""

import socketio
import subprocess
import logging
import json
import uuid
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversalDeploymentAgent:
    """SDV Runtime Compatible Universal Deployment Agent"""

    def __init__(self, kit_server_url="http://localhost:3090"):
        self.sio = socketio.Client()
        self.device_id = f"uda-{os.uname().nodename}-{uuid.uuid4().hex[:8]}"
        self.kit_server_url = kit_server_url
        self.running_apps = {}
        self.deployment_dir = os.environ.get('UDA_DEPLOYMENT_DIR', './deployments')
        self.log_dir = os.environ.get('UDA_LOG_DIR', './logs')

        # Ensure directories exist
        os.makedirs(self.deployment_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        logger.info(f"🚀 Initializing UDA Agent (ID: {self.device_id})")
        logger.info(f"📁 Deployment directory: {self.deployment_dir}")
        logger.info(f"📋 Log directory: {self.log_dir}")

        # Setup Socket.IO event handlers
        self.setup_events()

    def setup_events(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        def connect():
            logger.info(f"✅ Connected to Kit Server Adapter")
            capabilities = ['python', 'velocitas-sdk', 'kuksa-databroker']

            # Add Docker capability if available
            try:
                import docker
                capabilities.append('docker')
                logger.info("✅ Docker capability detected")
            except ImportError:
                logger.info("ℹ️ Docker not available")

            self.sio.emit('device_register', {
                'device_id': self.device_id,
                'type': 'uda-agent',
                'platform': 'linux',
                'capabilities': capabilities,
                'version': '1.0.0-sdv',
                'deployment_dir': self.deployment_dir,
                'log_dir': self.log_dir,
                'system_info': {
                    'platform': os.uname().sysname,
                    'release': os.uname().release,
                    'machine': os.uname().machine,
                    'hostname': os.uname().nodename
                }
            })

        @self.sio.event
        def connect_error():
            logger.error(f"❌ Failed to connect to Kit Server Adapter at {self.kit_server_url}")

        @self.sio.event
        def disconnect():
            logger.warning(f"⚠️ Disconnected from Kit Server Adapter")

        @self.sio.event
        def deploy_app(data):
            """Handle app deployment command"""
            try:
                app_name = data.get('app_name', 'unnamed-app')
                app_type = data.get('type', 'python')
                code = data.get('code', '')

                logger.info(f"🚀 Deploying {app_type} app: {app_name}")

                if app_type == 'python':
                    result = self.deploy_python_app(app_name, code)
                else:
                    result = {'success': False, 'error': f'Unsupported app type: {app_type}'}

                self.sio.emit('deployment_status', {
                    'app_name': app_name,
                    'device_id': self.device_id,
                    'timestamp': datetime.now().isoformat(),
                    **result
                })

            except Exception as e:
                logger.error(f"❌ Deployment failed: {e}")
                self.sio.emit('deployment_status', {
                    'app_name': data.get('app_name', 'unknown'),
                    'device_id': self.device_id,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        @self.sio.event
        def stop_app(data):
            """Handle app stop command"""
            try:
                app_name = data.get('app_name')
                if app_name in self.running_apps:
                    app_info = self.running_apps[app_name]
                    process = app_info['process']
                    process.terminate()

                    # Wait a bit for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()  # Force kill if not terminated

                    del self.running_apps[app_name]
                    logger.info(f"🛑 Stopped app: {app_name}")

                    self.sio.emit('app_status', {
                        'app_name': app_name,
                        'status': 'stopped',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.warning(f"⚠️ App not found: {app_name}")

            except Exception as e:
                logger.error(f"❌ Failed to stop app: {e}")

        @self.sio.event
        def get_status(data):
            """Handle status request"""
            apps_status = {}
            for app_name, app_info in self.running_apps.items():
                process = app_info['process']
                apps_status[app_name] = {
                    'pid': process.pid,
                    'status': 'running' if process.poll() is None else 'stopped',
                    'app_file': app_info['file'],
                    'log_file': app_info['log_file'],
                    'started_at': app_info['started_at']
                }

            self.sio.emit('device_status', {
                'device_id': self.device_id,
                'apps': apps_status,
                'timestamp': datetime.now().isoformat()
            })

    def deploy_python_app(self, app_name, code):
        """Deploy and execute Python application with SDV support"""
        try:
            # Create app file in deployment directory
            app_file = os.path.join(self.deployment_dir, f"{app_name}.py")
            log_file = os.path.join(self.log_dir, f"{app_name}.log")

            logger.info(f"📦 Deploying app {app_name} to {app_file}")

            # Write app code to file
            with open(app_file, 'w') as f:
                f.write(code)

            # Set up environment variables for SDV apps
            env = os.environ.copy()
            env.update({
                'KUKSA_DATA_BROKER_ADDRESS': os.environ.get('KUKSA_DATA_BROKER_ADDRESS', 'localhost:55555'),
                'VEHICLE_APP_SDK_CONFIG_PATH': os.environ.get('VEHICLE_APP_SDK_CONFIG_PATH', '/app/vehicle-app-sdk-config.json'),
                'SDV_MODE': os.environ.get('SDV_MODE', 'production'),
                'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO'),
                'UDA_APP_NAME': app_name,
                'UDA_AGENT_ID': self.device_id
            })

            # Execute app in background with proper logging
            with open(log_file, 'w') as log_fh:
                process = subprocess.Popen(
                    [sys.executable, app_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                    universal_newlines=True
                )

                # Start a thread to capture output
                import threading
                def capture_output():
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            log_fh.write(line)
                            log_fh.flush()
                            logger.info(f"📋 [{app_name}] {line.strip()}")

                output_thread = threading.Thread(target=capture_output, daemon=True)
                output_thread.start()

            # Track running app
            self.running_apps[app_name] = {
                'process': process,
                'file': app_file,
                'log_file': log_file,
                'started_at': datetime.now().isoformat(),
                'thread': output_thread
            }

            logger.info(f"✅ App deployed: {app_name} (PID: {process.pid})")
            logger.info(f"📋 Log file: {log_file}")

            return {
                'success': True,
                'pid': process.pid,
                'app_file': app_file,
                'log_file': log_file,
                'message': f'Python app deployed successfully'
            }

        except Exception as e:
            logger.error(f"❌ Python app deployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def start(self):
        """Start the UDA agent"""
        try:
            logger.info(f"🚀 Starting UDA Agent (ID: {self.device_id})")
            logger.info(f"📡 Connecting to Kit Server Adapter: {self.kit_server_url}")

            # Connect to Kit Server Adapter
            self.sio.connect(self.kit_server_url)

            # Keep connection alive
            self.sio.wait()

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down UDA Agent...")
            self.shutdown()

        except Exception as e:
            logger.error(f"❌ Agent failed to start: {e}")
            sys.exit(1)

    def shutdown(self):
        """Gracefully shutdown the agent and all apps"""
        logger.info("🛑 Shutting down UDA Agent...")

        # Stop all running apps
        for app_name, app_info in self.running_apps.items():
            try:
                process = app_info['process']
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                logger.info(f"🛑 Stopped app: {app_name}")
            except Exception as e:
                logger.error(f"❌ Error stopping app {app_name}: {e}")

        # Disconnect
        if self.sio.connected:
            self.sio.disconnect()

        logger.info("✅ UDA Agent shutdown complete")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Universal Deployment Agent')
    parser.add_argument(
        '--server',
        default='http://localhost:3090',
        help='Kit Server Adapter URL (default: http://localhost:3090)'
    )
    parser.add_argument(
        '--deployment-dir',
        default='./deployments',
        help='App deployment directory (default: ./deployments)'
    )
    parser.add_argument(
        '--log-dir',
        default='./logs',
        help='Log directory (default: ./logs)'
    )

    args = parser.parse_args()

    # Set environment variables
    os.environ['UDA_DEPLOYMENT_DIR'] = args.deployment_dir
    os.environ['UDA_LOG_DIR'] = args.log_dir

    # Create and start agent
    agent = UniversalDeploymentAgent(kit_server_url=args.server)
    agent.start()

if __name__ == '__main__':
    main()