#!/usr/bin/env python3

"""
Universal Deployment Agent
UDA for vehicle applications

Features:
- Socket.IO communication with Kit Server Adapter
- Full Velocitas SDK integration for KUKSA Data Broker
- Comprehensive error handling and logging
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
import time
import hashlib
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversalDeploymentAgent:
    """SDV Runtime Compatible Universal Deployment Agent"""

    def __init__(self, kit_server_url="https://kit.digitalauto.tech"):
        self.sio = socketio.Client()
        self.kit_server_url = kit_server_url
        self.running_apps = {}
        self.deployment_dir = os.environ.get('UDA_DEPLOYMENT_DIR', './deployments')
        self.log_dir = os.environ.get('UDA_LOG_DIR', './logs')
        self.runtime_file = os.path.join(os.path.dirname(__file__), '.runtime_name')

        # Ensure directories exist
        os.makedirs(self.deployment_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Load or generate runtime name
        self.runtime_name = self._get_or_generate_runtime_name()
        self.device_id = f"Runtime-{self.runtime_name}"

        # Track active requests for stdout streaming
        self.active_requests = {}  # {request_id: {app_name, cmd, request_from}}

        logger.info(f"🚀 Initializing UDA Agent")
        logger.info(f"🏷️  Runtime Name: {self.runtime_name}")
        logger.info(f"🆔 Kit ID: {self.device_id}")
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

            self.sio.emit('register_kit', {
                'kit_id': self.device_id,
                'name': self.runtime_name,
                'type': 'uda-agent',
                'platform': 'linux',
                'capabilities': capabilities,
                'version': '1.0.0-sdv',
                'support_apis': ['python', 'velocitas-sdk', 'kuksa-databroker', 'docker'],
                'desc': 'Universal Deployment Agent for SD vehicle applications'
            })

        @self.sio.event
        def connect_error(data):
            logger.error(f"❌ Failed to connect to Kit Server Adapter at {self.kit_server_url}: {data}")

        @self.sio.event
        def disconnect():
            logger.warning(f"⚠️ Disconnected from Kit Server Adapter")

        @self.sio.event
        def register_kit_ack(data):
            logger.info(f"✅ Runtime registration acknowledged by Kit Server")
            logger.info(f"📋 Runtime '{self.runtime_name}' is now online and discoverable")

        # SDV Runtime Compatible Event Handlers
        @self.sio.event
        def messageToKit(data):
            """Handle SDV runtime compatible messages"""
            try:
                cmd = data.get('cmd', '')
                request_from = data.get('request_from', 'unknown')

                logger.info(f"📨 SDV Runtime Command: {cmd}")

                if cmd in ['deploy_request', 'deploy_n_run', 'run_python_app']:
                    self._handle_sdv_deploy(data, request_from)
                elif cmd == 'stop_python_app':
                    self._handle_sdv_stop(data, request_from)
                elif cmd == 'get-runtime-info':
                    self._handle_sdv_status(data, request_from)
                else:
                    logger.warning(f"⚠️ Unknown SDV command: {cmd}")
                    self._send_sdv_response(request_from, cmd, "Unknown command", False, 1)

            except Exception as e:
                logger.error(f"❌ Error handling SDV message: {e}")
                request_from = data.get('request_from', 'unknown')
                cmd = data.get('cmd', 'unknown')
                self._send_sdv_response(request_from, cmd, str(e), False, 1)

        # Catch-all event listener for debugging (must be last)
        @self.sio.on('*')
        def catch_all(event, data):
            logger.info(f"📨 Kit Server Event: {event}")
            if data:
                logger.debug(f"📦 Data: {data}")

    # Kit Server Compatible Helper Methods
    def send_kit_server_reply(self, request_from, cmd, result, is_done=True, code=0, token=None):
        """Send Kit Server compatible messageToKit-kitReply response"""
        message = {
            'kit_id': self.device_id,
            'request_from': request_from,
            'cmd': cmd,
            'data': '',
            'result': result,
            'isDone': is_done,
            'code': code
        }

        # Add token for deployment operations
        if token:
            message['token'] = token

        logger.info(f"📤 Sending Kit Server reply: {cmd} -> {result[:100]}{'...' if len(result) > 100 else ''}")
        print(f"🐛 DEBUG: About to emit messageToKit-kitReply event")
        self.sio.emit('messageToKit-kitReply', message)
        print(f"🐛 DEBUG: messageToKit-kitReply event emitted successfully")

    def send_deployment_status(self, request_from, app_name, status_message, token=None, is_finish=False):
        """Send deployment status update"""
        message = f"Deploying {app_name}: {status_message}"
        self.send_kit_server_reply(request_from, 'deploy_request', message, is_finish=is_finish, code=0, token=token)

    def send_app_output(self, request_from, app_name, output_line, cmd='run_python_app'):
        """Send real-time app output line"""
        # Format output line with app context
        formatted_output = f"[{app_name}] {output_line.rstrip()}"
        self.send_kit_server_reply(request_from, cmd, formatted_output, is_done=False, code=0)

    def send_runtime_state(self):
        """Send runtime state update"""
        state_data = {
            'noOfRunner': len(self.running_apps),
            'noOfApiSubscriber': 0,  # Could be implemented later
            'apps': list(self.running_apps.keys())
        }

        message = {
            'kit_id': self.device_id,
            'data': state_data
        }

        logger.info(f"📊 Sending runtime state: {len(self.running_apps)} running apps")
        self.sio.emit('report-runtime-state', message)

    def stream_app_output(self, request_from, app_name, process, cmd='run_python_app'):
        """Stream app output in real-time using proper Kit Server format"""
        import threading
        import queue

        output_queue = queue.Queue()

        def stdout_reader():
            """Read stdout and put lines in queue"""
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        output_queue.put(('stdout', line))
            except Exception as e:
                logger.error(f"❌ Error reading stdout for {app_name}: {e}")
            finally:
                output_queue.put(('done', None))

        def stderr_reader():
            """Read stderr and put lines in queue"""
            try:
                for line in iter(process.stderr.readline, ''):
                    if line:
                        output_queue.put(('stderr', line))
            except Exception as e:
                logger.error(f"❌ Error reading stderr for {app_name}: {e}")
            finally:
                output_queue.put(('done', None))

        def output_streamer():
            """Stream output to Kit Server"""
            readers_done = 0
            while readers_done < 2:
                try:
                    stream_type, line = output_queue.get(timeout=1)
                    if stream_type == 'done':
                        readers_done += 1
                    elif line:
                        # Send each line immediately to Kit Server
                        prefix = f"[{app_name}:{stream_type.upper()}]"
                        formatted_line = f"{prefix} {line.rstrip()}"
                        self.send_app_output(request_from, app_name, formatted_line, cmd)

                        # Also log locally
                        logger.info(f"📋 {formatted_line}")

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error streaming output for {app_name}: {e}")
                    break

        # Start reader threads
        stdout_thread = threading.Thread(target=stdout_reader, daemon=True)
        stderr_thread = threading.Thread(target=stderr_reader, daemon=True)
        streamer_thread = threading.Thread(target=output_streamer, daemon=True)

        stdout_thread.start()
        stderr_thread.start()
        streamer_thread.start()

        return {
            'stdout_thread': stdout_thread,
            'stderr_thread': stderr_thread,
            'streamer_thread': streamer_thread,
            'output_queue': output_queue
        }

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

    def _handle_sdv_deploy(self, data, request_from):
        """Handle SDV runtime app deployment"""
        try:
            cmd = data.get('cmd', '')
            app_name = data.get('name', 'sdv-app')

            # Get code - try convertedCode first, then code
            code = data.get('convertedCode') or data.get('code', '')

            if not code:
                self._send_sdv_response(request_from, cmd, "No code provided", False, 1)
                return

            logger.info(f"🚀 SDV Deploying app: {app_name}")

            # Write code to main.py
            app_file = os.path.join(self.deployment_dir, f"{app_name}-main.py")
            with open(app_file, 'w') as f:
                f.write(code)

            # Generate deployment token
            import uuid
            deployment_token = str(uuid.uuid4())[:8]

            # Send initial deployment status
            self.send_deployment_status(request_from, app_name, "Starting deployment", deployment_token, False)

            # Execute the app
            log_file = os.path.join(self.log_dir, f"{app_name}.log")

            # Set up environment variables
            env = os.environ.copy()
            env.update({
                'KUKSA_DATA_BROKER_ADDRESS': os.environ.get('KUKSA_DATA_BROKER_ADDRESS', 'localhost:55555'),
                'UDA_APP_NAME': app_name,
                'UDA_AGENT_ID': self.device_id
            })

            # Execute with python -u for unbuffered output
            process = subprocess.Popen(
                [sys.executable, '-u', app_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                universal_newlines=True
            )

            self.send_deployment_status(request_from, app_name, f"Process started (PID: {process.pid})", deployment_token, False)

            # Start real-time output streaming to Kit Server
            stream_info = self.stream_app_output(request_from, app_name, process, cmd)

            # Track running app
            self.running_apps[app_name] = {
                'process': process,
                'file': app_file,
                'log_file': log_file,
                'started_at': datetime.now().isoformat(),
                'stream_info': stream_info,
                'cmd': cmd,
                'request_from': request_from,
                'deployment_token': deployment_token
            }

            # Send runtime state update
            self.send_runtime_state()

            # Send final deployment status
            self.send_deployment_status(request_from, app_name, "Deployment completed", deployment_token, True)

            logger.info(f"✅ SDV App deployed: {app_name} (PID: {process.pid}) - Streaming output enabled")

            # Send success response
            if cmd == 'run_python_app':
                self._send_sdv_response(request_from, cmd, f"App started successfully", True, 0)
            else:
                self._send_sdv_response(request_from, cmd, f"App deployed successfully", True, 0)

        except Exception as e:
            logger.error(f"❌ SDV Deployment failed: {e}")
            self._send_sdv_response(request_from, cmd, str(e), False, 1)

    def _handle_sdv_stop(self, data, request_from):
        """Handle SDV runtime app stop"""
        try:
            app_name = data.get('name', 'unknown')
            cmd = data.get('cmd', 'stop_python_app')

            if app_name in self.running_apps:
                app_info = self.running_apps[app_name]
                process = app_info['process']
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                del self.running_apps[app_name]
                logger.info(f"🛑 SDV App stopped: {app_name}")

                self._send_sdv_response(request_from, cmd, f"App {app_name} stopped successfully", True, 0)
            else:
                self._send_sdv_response(request_from, cmd, f"App {app_name} not found", False, 1)

        except Exception as e:
            logger.error(f"❌ SDV Stop failed: {e}")
            self._send_sdv_response(request_from, cmd, str(e), False, 1)

    def _handle_sdv_status(self, data, request_from):
        """Handle SDV runtime status request"""
        try:
            apps_info = []
            for app_name, app_info in self.running_apps.items():
                process = app_info['process']
                apps_info.append({
                    'name': app_name,
                    'pid': process.pid,
                    'status': 'running' if process.poll() is None else 'stopped',
                    'started_at': app_info['started_at']
                })

            status_data = {
                'runtime_id': self.device_id,
                'runtime_name': self.runtime_name,
                'apps': apps_info,
                'status': 'online'
            }

            # Send status response using Kit Server compatible format
            self.send_kit_server_reply(request_from, 'get-runtime-info', json.dumps(status_data), is_done=True, code=0)

            logger.info(f"📊 SDV Runtime status sent")

        except Exception as e:
            logger.error(f"❌ SDV Status failed: {e}")
            self._send_sdv_response(request_from, 'get-runtime-info', str(e), False, 1)

    def _send_sdv_response(self, request_from, cmd, result, success, return_code):
        """Send SDV runtime compatible response"""
        print(f"🐛 DEBUG: _send_sdv_response called - about to call send_kit_server_reply")
        self.send_kit_server_reply(request_from, cmd, result, is_done=True, code=return_code)
        logger.info(f"📤 SDV Response sent: {cmd} -> {result}")

    def _get_or_generate_runtime_name(self):
        """Load existing runtime name from file or generate new one"""
        # Check if RUNTIME_NAME is set in environment
        env_runtime_name = os.environ.get('RUNTIME_NAME')
        if env_runtime_name:
            logger.info(f"🏷️  Using runtime name from environment: {env_runtime_name}")
            return env_runtime_name

        # Try to load from file
        if os.path.exists(self.runtime_file):
            try:
                with open(self.runtime_file, 'r') as f:
                    saved_runtime_name = f.read().strip()
                if saved_runtime_name:
                    logger.info(f"📂 Loaded runtime name from file: {saved_runtime_name}")
                    return saved_runtime_name
            except Exception as e:
                logger.warning(f"⚠️ Could not read runtime file: {e}")

        # Generate new runtime name
        runtime_hash = hashlib.sha256(f"{os.uname().nodename}-{time.time()}".encode()).hexdigest()[:8]
        new_runtime_name = f'UDA-{runtime_hash}'

        # Save to file
        try:
            with open(self.runtime_file, 'w') as f:
                f.write(new_runtime_name)
            logger.info(f"💾 Saved new runtime name to file: {new_runtime_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save runtime file: {e}")

        logger.info(f"🆕 Generated new runtime name: {new_runtime_name}")
        return new_runtime_name

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
                'SDV_MODE': os.environ.get('SDV_MODE', 'standard'),
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
        default='https://kit.digitalauto.tech',
        help='Kit Server Adapter URL (default: https://kit.digitalauto.tech)'
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