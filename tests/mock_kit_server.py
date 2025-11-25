#!/usr/bin/env python3

"""
Mock Kit Server Adapter for UDA Testing
Isolated testing environment - no external dependencies
"""

import asyncio
import json
import logging
import os
import socket
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import socketio
from aiohttp import web, ClientSession

class MockKitServerAdapter:
    """Simplified Kit Server Adapter for UDA testing"""

    def __init__(self):
        self.host = os.getenv('ADAPTER_HOST', '0.0.0.0')
        self.port = int(os.getenv('ADAPTER_PORT', '3090'))
        self.device_id = os.getenv('DEVICE_ID', f'test-device-{socket.gethostname()}')

        # Test state management
        self.registered_devices: Dict[str, dict] = {}
        self.deployed_apps: Dict[str, List[dict]] = {}
        self.test_results: List[dict] = []

        # Socket.IO server
        self.sio = socketio.AsyncServer(
            cors_allowed_origins='*',
            logger=False,
            engineio_logger=False
        )

        self.setup_logging()
        self.logger = logging.getLogger(__name__)

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def setup_socketio_events(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        async def connect(sid, environ):
            """Handle new UDA agent connection"""
            self.logger.info(f"📱 UDA agent connected: {sid}")
            device_id = f"device-{len(self.registered_devices) + 1}"

            self.registered_devices[device_id] = {
                'sid': sid,
                'id': device_id,
                'connected_at': datetime.now().isoformat(),
                'status': 'connected',
                'remote': environ.get('REMOTE_ADDR', 'unknown')
            }

            # Send welcome message
            await self.sio.emit('connected', {
                'server': 'MockKitServer',
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            }, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle UDA agent disconnection"""
            self.logger.info(f"📱 UDA agent disconnected: {sid}")

            # Find and update device
            for device_id, device in self.registered_devices.items():
                if device.get('sid') == sid:
                    device['status'] = 'disconnected'
                    device['disconnected_at'] = datetime.now().isoformat()
                    break

        @self.sio.event
        async def heartbeat(sid, data):
            """Handle heartbeat from UDA agent"""
            await self.sio.emit('heartbeat_response', {
                'timestamp': datetime.now().isoformat()
            }, room=sid)

        @self.sio.event
        async def app_status(sid, data):
            """Handle app status updates from UDA agent"""
            app_id = data.get('app_id', 'unknown')
            status = data.get('status', 'unknown')

            # Find device ID
            device_id = 'unknown'
            for did, device in self.registered_devices.items():
                if device.get('sid') == sid:
                    device_id = did
                    break

            self.logger.info(f"📊 App {app_id} on {device_id}: {status}")

            # Record test result
            self.test_results.append({
                'device_id': device_id,
                'app_id': app_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            })

    async def start_server(self):
        """Start the mock Kit Server"""
        self.logger.info(f"🧪 Starting Mock Kit Server Adapter on {self.host}:{self.port}")
        self.logger.info(f"   Device ID: {self.device_id}")
        self.logger.info(f"   Mode: Testing (Isolated)")

        # Setup Socket.IO events
        self.setup_socketio_events()

        app = web.Application()
        self.sio.attach(app)

        app.add_routes([
            web.get('/health', self.health_check),
            web.get('/api/v1/health', self.health_check),
            web.post('/api/v1/devices/register', self.register_device),
            web.get('/api/v1/devices', self.list_devices),
            web.post('/api/v1/apps/deploy', self.deploy_app),
            web.get('/api/v1/apps', self.list_apps),
            web.post('/api/v1/apps/{app_id}/stop', self.stop_app),
            web.get('/api/v1/test/results', self.get_test_results),
        ])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        self.logger.info("✅ Mock Kit Server Adapter started successfully")
        self.logger.info("   Ready for UDA testing!")

        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("🛑 Shutting down Mock Kit Server...")

    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'mode': 'testing',
            'devices': len(self.registered_devices),
            'apps': sum(len(apps) for apps in self.deployed_apps.values())
        })

    async def deploy_app_via_socketio(self, device_id: str, app_config: dict):
        """Deploy app via Socket.IO to connected agent"""
        app_id = app_config.get('app_name', f'app-{int(time.time())}')

        # Find device SID
        device_sid = None
        for did, device in self.registered_devices.items():
            if did == device_id and device.get('status') == 'connected':
                device_sid = device.get('sid')
                break

        if not device_sid:
            self.logger.error(f"❌ Device {device_id} not connected for app deployment")
            return False

        self.logger.info(f"🚀 Deploying app {app_id} to {device_id} via Socket.IO")

        # Send deployment command via Socket.IO
        await self.sio.emit('deploy_app', app_config, room=device_sid)

        # Record deployment
        if device_id not in self.deployed_apps:
            self.deployed_apps[device_id] = []

        deployment = {
            'app_id': app_id,
            'config': app_config,
            'deployed_at': datetime.now().isoformat(),
            'status': 'deployed'
        }
        self.deployed_apps[device_id].append(deployment)

        return True

    async def register_device(self, request):
        """Device registration endpoint"""
        data = await request.json()
        device_id = data.get('device_id', self.device_id)

        self.registered_devices[device_id] = {
            **data,
            'id': device_id,
            'registered_at': datetime.now().isoformat(),
            'status': 'registered'
        }

        self.logger.info(f"📝 Device registered: {device_id}")

        return web.json_response({
            'success': True,
            'device_id': device_id,
            'message': 'Device registered successfully'
        })

    async def list_devices(self, request):
        """List registered devices"""
        return web.json_response({
            'devices': list(self.registered_devices.values()),
            'count': len(self.registered_devices)
        })

    async def deploy_app(self, request):
        """App deployment endpoint"""
        data = await request.json()
        device_id = data.get('device_id')
        app_config = data.get('app')
        app_id = app_config.get('app_name', f'app-{int(time.time())}')

        self.logger.info(f"🚀 Deploying app {app_id} to {device_id}")

        # Find device SID and deploy via Socket.IO
        device_sid = None
        for did, device in self.registered_devices.items():
            if did == device_id and device.get('status') == 'connected':
                device_sid = device.get('sid')
                break

        if not device_sid:
            return web.json_response({
                'success': False,
                'error': f'Device {device_id} not connected'
            }, status=404)

        # Send deployment command via Socket.IO
        await self.sio.emit('deploy_app', app_config, room=device_sid)

        # Initialize device apps list if needed
        if device_id not in self.deployed_apps:
            self.deployed_apps[device_id] = []

        # Record deployment
        deployment = {
            'app_id': app_id,
            'config': app_config,
            'deployed_at': datetime.now().isoformat(),
            'status': 'deployed'
        }
        self.deployed_apps[device_id].append(deployment)

        return web.json_response({
            'success': True,
            'app_id': app_id,
            'device_id': device_id,
            'message': f'App {app_id} deployed successfully to {device_id}',
            'deployment_id': f"deploy-{len(self.test_results)}"
        })

    async def list_apps(self, request):
        """List deployed apps"""
        device_id = request.query.get('device_id')

        if device_id:
            apps = self.deployed_apps.get(device_id, [])
        else:
            # Flatten all apps from all devices
            apps = []
            for device_apps in self.deployed_apps.values():
                apps.extend(device_apps)

        return web.json_response({
            'apps': apps,
            'count': len(apps)
        })

    async def stop_app(self, request):
        """Stop running app"""
        app_id = request.match_info['app_id']
        data = await request.json()
        device_id = data.get('device_id')

        self.logger.info(f"🛑 Stopping app {app_id} on {device_id}")

        # Update app status
        if device_id in self.deployed_apps:
            for app in self.deployed_apps[device_id]:
                if app['app_id'] == app_id:
                    app['status'] = 'stopped'
                    app['stopped_at'] = datetime.now().isoformat()
                    break

        return web.json_response({
            'success': True,
            'message': f'App {app_id} stopped on {device_id}'
        })

    async def get_test_results(self, request):
        """Get test results for verification"""
        return web.json_response({
            'test_results': self.test_results,
            'devices': self.registered_devices,
            'deployments': self.deployed_apps,
            'summary': {
                'total_tests': len(self.test_results),
                'devices_registered': len(self.registered_devices),
                'apps_deployed': sum(len(apps) for apps in self.deployed_apps.values())
            }
        })

async def main():
    """Main function"""
    adapter = MockKitServerAdapter()
    await adapter.start_server()

if __name__ == "__main__":
    asyncio.run(main())