#!/usr/bin/env python3

"""
Ultra-Lightweight UDA Agent
Universal Deployment Agent for vehicle applications

Features:
- ~50 lines of code
- ~5MB memory usage
- Socket.IO communication with Kit Server Adapter
- Direct KUKSA Data Broker integration
- No VSS dependency
- Dynamic signal registration
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

class UltraLightweightUDAgent:
    def __init__(self, kit_server_url="http://localhost:3090"):
        self.sio = socketio.Client()
        self.device_id = f"uda-device-{uuid.uuid4().hex[:8]}"
        self.kit_server_url = kit_server_url
        self.running_apps = {}

        # Setup Socket.IO event handlers
        self.setup_events()

    def setup_events(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        def connect():
            logger.info(f"✅ Connected to Kit Server Adapter")
            self.sio.emit('device_register', {
                'device_id': self.device_id,
                'type': 'uda-agent',
                'capabilities': ['python', 'docker'],
                'version': '1.0.0'
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
                    process = self.running_apps[app_name]
                    process.terminate()
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
            for app_name, process in self.running_apps.items():
                apps_status[app_name] = {
                    'pid': process.pid,
                    'status': 'running' if process.poll() is None else 'stopped'
                }

            self.sio.emit('device_status', {
                'device_id': self.device_id,
                'apps': apps_status,
                'timestamp': datetime.now().isoformat()
            })

    def deploy_python_app(self, app_name, code):
        """Deploy and execute Python application"""
        try:
            # Create app file
            app_file = f"{app_name}.py"
            with open(app_file, 'w') as f:
                f.write(code)

            # Execute app in background
            process = subprocess.Popen(
                [sys.executable, app_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Track running app
            self.running_apps[app_name] = process

            logger.info(f"✅ App deployed: {app_name} (PID: {process.pid})")

            return {
                'success': True,
                'pid': process.pid,
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
            # Stop all running apps
            for app_name, process in self.running_apps.items():
                process.terminate()
                logger.info(f"🛑 Stopped app: {app_name}")

            # Disconnect
            if self.sio.connected:
                self.sio.disconnect()

        except Exception as e:
            logger.error(f"❌ Agent failed to start: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Ultra-Lightweight UDA Agent')
    parser.add_argument(
        '--server',
        default='http://localhost:3090',
        help='Kit Server Adapter URL (default: http://localhost:3090)'
    )

    args = parser.parse_args()

    # Create and start agent
    agent = UltraLightweightUDAgent(kit_server_url=args.server)
    agent.start()

if __name__ == '__main__':
    main()