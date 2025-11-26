#!/usr/bin/env python3
"""
Mock Kit Server for testing UDA agent
"""

import socketio
import threading
import time
import json
from datetime import datetime

class MockKitServer:
    def __init__(self, port=3091):  # Use different port to avoid conflict
        self.port = port
        self.sio = socketio.Server(cors_allowed_origins="*", logger=True, engineio_logger=True)
        self.connected_clients = {}
        self.registered_kits = {}

    def setup_events(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        def connect(sid, environ):
            print(f"🔌 Client connected: {sid}")
            self.connected_clients[sid] = {
                'connected_at': datetime.now().isoformat(),
                'sid': sid
            }

        @self.sio.event
        def disconnect(sid):
            print(f"❌ Client disconnected: {sid}")
            if sid in self.connected_clients:
                del self.connected_clients[sid]

            # Remove from registered kits if it was a kit
            for kit_id, kit_info in list(self.registered_kits.items()):
                if kit_info.get('socket_id') == sid:
                    kit_info['is_online'] = False
                    print(f"📡 Kit went offline: {kit_id}")

        @self.sio.event
        def register_kit(sid, data):
            """Handle kit registration"""
            kit_id = data.get('kit_id')
            name = data.get('name')
            kit_type = data.get('type', 'unknown')

            print(f"🏷️  Kit registered: {kit_id} ({name})")

            # Store kit info
            self.registered_kits[kit_id] = {
                'kit_id': kit_id,
                'name': name,
                'type': kit_type,
                'socket_id': sid,
                'connected_at': datetime.now().isoformat(),
                'is_online': True,
                'capabilities': data.get('capabilities', []),
                'support_apis': data.get('support_apis', []),
                'platform': data.get('platform', 'unknown'),
                'version': data.get('version', '1.0.0'),
                'desc': data.get('desc', '')
            }

            # Send acknowledgment
            self.sio.emit('register_kit_ack', {
                'kit_id': kit_id,
                'status': 'registered',
                'message': f'Kit {kit_id} registered successfully'
            }, room=sid)

        @self.sio.event
        def messageToKit(sid, data):
            """Handle messageToKit - route to appropriate kit"""
            cmd = data.get('cmd', '')
            target_kit_id = data.get('to_kit_id', '')
            request_from = data.get('request_from', 'unknown')

            print(f"📨 Received command '{cmd}' for kit '{target_kit_id}' from {request_from}")

            # Find the target kit
            if target_kit_id in self.registered_kits:
                kit_info = self.registered_kits[target_kit_id]
                target_sid = kit_info['socket_id']

                print(f"🎯 Forwarding message to kit: {target_kit_id} (sid: {target_sid})")

                # Forward the message to the target kit
                self.sio.emit('messageToKit', data, room=target_sid)

                # Store request info for routing response back
                kit_info['active_request'] = {
                    'request_from': request_from,
                    'cmd': cmd,
                    'original_sid': sid
                }
            else:
                print(f"❌ Kit not found: {target_kit_id}")
                # Send error response back to requester
                error_response = {
                    'request_from': request_from,
                    'cmd': cmd,
                    'result': f'Kit not found: {target_kit_id}',
                    'is_finish': True,
                    'code': 1,
                    'isDone': True
                }
                self.sio.emit('messageToKit', error_response, room=sid)

        @self.sio.on('*')
        def catch_all(event, sid, data):
            """Log all events for debugging"""
            if event not in ['connect', 'disconnect', 'messageToKit']:
                print(f"📨 Received event '{event}' from {sid}")
                if isinstance(data, dict) and len(str(data)) < 300:
                    print(f"📦 Data: {json.dumps(data, indent=2)}")

            # Handle responses from UDA agent and route back to original client
            if event == 'messageToKit' and sid in [kit['socket_id'] for kit in self.registered_kits.values()]:
                # This is a message from a UDA agent
                message = data
                cmd = message.get('cmd', '')
                request_from = message.get('request_from', '')

                # Find which kit sent this message
                kit_id = None
                for kid, kit_info in self.registered_kits.items():
                    if kit_info['socket_id'] == sid:
                        kit_id = kid
                        break

                # Check if this kit has an active request
                if kit_id and 'active_request' in self.registered_kits[kit_id]:
                    original_sid = self.registered_kits[kit_id]['active_request']['original_sid']
                    original_cmd = self.registered_kits[kit_id]['active_request']['cmd']

                    # Check if this looks like a response (has result field OR has is_finish=true)
                    is_response = ('result' in message) or message.get('is_finish', False) or message.get('isDone', False)

                    if is_response and cmd == original_cmd:
                        print(f"🎯 Routing response from UDA agent '{kit_id}' back to test client (sid: {original_sid})")
                        print(f"📦 Response: {message}")

                        # Send response back to original test client
                        self.sio.emit('messageToKit', message, room=original_sid)

                        # Clear active request
                        del self.registered_kits[kit_id]['active_request']
                    else:
                        print(f"⚠️ Ignoring message from kit '{kit_id}' - not matching response pattern")
                else:
                    print(f"⚠️ Message from kit '{kit_id}' but no active request - ignoring")

    def start_server(self):
        """Start the mock Kit Server"""
        self.setup_events()

        print(f"🚀 Starting Mock Kit Server on port {self.port}")
        print(f"📡 Server will be available at: http://localhost:{self.port}")
        print("=" * 50)

        # Wrap the app with WSGI middleware
        app = socketio.WSGIApp(self.sio)

        # Start server with eventlet
        import eventlet
        eventlet.wsgi.server(eventlet.listen(('', self.port)), app)

    def print_status(self):
        """Print current server status"""
        print(f"\n📊 Mock Kit Server Status:")
        print(f"   Connected clients: {len(self.connected_clients)}")
        print(f"   Registered kits: {len(self.registered_kits)}")

        if self.registered_kits:
            print(f"\n📝 Registered Kits:")
            for kit_id, kit_info in self.registered_kits.items():
                status = "🟢 Online" if kit_info['is_online'] else "🔴 Offline"
                print(f"   • {kit_id} ({kit_info['name']}) - {status}")
                print(f"     Type: {kit_info['type']}, Platform: {kit_info['platform']}")
                if kit_info['capabilities']:
                    print(f"     Capabilities: {', '.join(kit_info['capabilities'])}")

def main():
    """Main function to run the mock server"""
    server = MockKitServer(port=3091)

    # Start status monitoring thread
    def status_monitor():
        while True:
            time.sleep(10)
            server.print_status()

    status_thread = threading.Thread(target=status_monitor, daemon=True)
    status_thread.start()

    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Mock Kit Server stopped by user")
    except Exception as e:
        print(f"❌ Mock Kit Server error: {e}")

if __name__ == "__main__":
    print("🧪 Mock Kit Server for UDA Agent Testing")
    print("=" * 50)

    main()