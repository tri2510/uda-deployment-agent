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
        self.sio = socketio.Server(cors_allowed_origins="*")
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
            """Handle messageToKit - route requests and responses"""
            cmd = data.get('cmd', '')
            target_kit_id = data.get('to_kit_id', '')
            request_from = data.get('request_from', 'unknown')

            # Determine if this is a request from test client or response from UDA agent
            is_response = ('result' in data) or data.get('is_finish', False) or data.get('isDone', False)

            if is_response:
                # This is a response from UDA agent - route it back to the original test client
                print(f"📨 Received response '{cmd}' from UDA agent")

                # Find which kit sent this response
                kit_id = None
                kit_info = None
                for kid, info in self.registered_kits.items():
                    if info['socket_id'] == sid:
                        kit_id = kid
                        kit_info = info
                        break

                if kit_id and kit_info and 'active_request' in kit_info:
                    original_sid = kit_info['active_request']['original_sid']
                    original_cmd = kit_info['active_request']['cmd']

                    if cmd == original_cmd:
                        print(f"🎯 Routing response from UDA agent '{kit_id}' back to test client (sid: {original_sid})")
                        print(f"📦 Response: {json.dumps(data, indent=2)}")

                        # Send response back to original test client
                        self.sio.emit('messageToKit', data, room=original_sid)

                        # Clear active request
                        del kit_info['active_request']
                    else:
                        print(f"⚠️ Response command mismatch: expected {original_cmd}, got {cmd}")
                else:
                    print(f"⚠️ Received response but no active request found for kit {kit_id}")
            else:
                # This is a request from test client - forward it to UDA agent
                print(f"📨 Received request '{cmd}' for kit '{target_kit_id}' from {request_from}")

                # Find the target kit
                if target_kit_id in self.registered_kits:
                    kit_info = self.registered_kits[target_kit_id]
                    target_sid = kit_info['socket_id']

                    print(f"🎯 Forwarding request to kit: {target_kit_id} (sid: {target_sid})")

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

        @self.sio.event
        def messageToKit_kitReply(sid, data):
            """Handle messageToKit-kitReply - route UDA agent SDV-runtime responses back to test clients"""
            cmd = data.get('cmd', '')
            request_from = data.get('request_from', 'unknown')
            kit_id = data.get('kit_id', '')
            result = data.get('result', '')
            is_done = data.get('isDone', True)
            code = data.get('code', 0)

            print(f"📨 Received SDV runtime response '{cmd}' (kit: {kit_id[:15]}...)")
            print(f"   Request from: {request_from}")
            print(f"   Is Done: {is_done}, Code: {code}")

            # Find which kit sent this response
            kit_info = None
            for kid, info in self.registered_kits.items():
                if info['socket_id'] == sid:
                    kit_info = info
                    break

            if kit_info and 'active_request' in kit_info:
                # Route response back to original test client
                original_request = kit_info['active_request']
                test_client_sid = original_request['original_sid']

                print(f"🎯 Routing response back to test client: {test_client_sid}")
                self.sio.emit('messageToKit-kitReply', data, room=test_client_sid)

                # Clear active request if this is the final response
                if is_done:
                    kit_info.pop('active_request', None)
            else:
                print(f"⚠️ No active request found for kit {kit_id}, broadcasting to all clients")
                self.sio.emit('messageToKit-kitReply', data)

        @self.sio.on('*')
        def catch_all(event, sid, data):
            """Log all events for debugging"""
            if event not in ['connect', 'disconnect', 'messageToKit', 'messageToKit-kitReply', 'register_kit']:
                print(f"📨 Received event '{event}' from {sid}")
                if isinstance(data, dict) and len(str(data)) < 300:
                    print(f"📦 Data: {json.dumps(data, indent=2)}")

    def start_server(self):
        """Start the mock Kit Server"""
        self.setup_events()

        print(f"🚀 Starting Mock Kit Server on port {self.port}")
        print(f"📡 Server will be available at: http://localhost:{self.port}")
        print("=" * 50)

        # Create a simple WSGI application
        def simple_wsgi_app(environ, start_response):
            """Simple WSGI app that returns 404 for HTTP requests"""
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Not Found - This is a Socket.IO server only']

        # Wrap with Socket.IO WSGI app
        app = socketio.WSGIApp(self.sio, simple_wsgi_app)

        # Try to start server with eventlet first, fallback to wsgiref
        try:
            import eventlet
            eventlet.wsgi.server(eventlet.listen(('', self.port)), app)
        except ImportError:
            print("⚠️ eventlet not available, using wsgiref (less performant)")
            from wsgiref.simple_server import make_server
            httpd = make_server('', self.port, app)
            print(f"🌐 Starting server with wsgiref on port {self.port}")
            httpd.serve_forever()

    def copy_events_to_flask_socketio(self, sio_app):
        """Copy event handlers to Flask-SocketIO app"""

        @sio_app.event
        def connect(sid, environ):
            print(f"🔌 Client connected: {sid}")
            self.connected_clients[sid] = {
                'connected_at': datetime.now().isoformat(),
                'sid': sid
            }

        @sio_app.event
        def disconnect(sid):
            print(f"❌ Client disconnected: {sid}")
            if sid in self.connected_clients:
                del self.connected_clients[sid]

            # Remove from registered kits if it was a kit
            for kit_id, kit_info in list(self.registered_kits.items()):
                if kit_info.get('socket_id') == sid:
                    kit_info['is_online'] = False
                    print(f"📡 Kit went offline: {kit_id}")

        @sio_app.event
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
            sio_app.emit('register_kit_ack', {
                'kit_id': kit_id,
                'status': 'registered',
                'message': f'Kit {kit_id} registered successfully'
            }, room=sid)

        @sio_app.event
        def messageToKit(sid, data):
            """Handle messageToKit - route requests and responses"""
            cmd = data.get('cmd', '')
            target_kit_id = data.get('to_kit_id', '')
            request_from = data.get('request_from', 'unknown')

            # Determine if this is a request from test client or response from UDA agent
            is_response = ('result' in data) or data.get('is_finish', False) or data.get('isDone', False)

            if is_response:
                # This is a response from UDA agent - route it back to the original test client
                print(f"📨 Received response '{cmd}' from UDA agent")

                # Find which kit sent this response
                kit_id = None
                kit_info = None
                for kid, info in self.registered_kits.items():
                    if info['socket_id'] == sid:
                        kit_id = kid
                        kit_info = info
                        break

                if kit_id and kit_info and 'active_request' in kit_info:
                    original_sid = kit_info['active_request']['original_sid']
                    original_cmd = kit_info['active_request']['cmd']

                    if cmd == original_cmd:
                        print(f"🎯 Routing response from UDA agent '{kit_id}' back to test client (sid: {original_sid})")
                        print(f"📦 Response: {json.dumps(data, indent=2)}")

                        # Send response back to original test client
                        sio_app.emit('messageToKit', data, room=original_sid)

                        # Clear active request
                        del kit_info['active_request']
                    else:
                        print(f"⚠️ Response command mismatch: expected {original_cmd}, got {cmd}")
                else:
                    print(f"⚠️ Received response but no active request found for kit {kit_id}")
            else:
                # This is a request from test client - forward it to UDA agent
                print(f"📨 Received request '{cmd}' for kit '{target_kit_id}' from {request_from}")

                # Find the target kit
                if target_kit_id in self.registered_kits:
                    kit_info = self.registered_kits[target_kit_id]
                    target_sid = kit_info['socket_id']

                    print(f"🎯 Forwarding request to kit: {target_kit_id} (sid: {target_sid})")

                    # Forward the message to the target kit
                    sio_app.emit('messageToKit', data, room=target_sid)

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
                    sio_app.emit('messageToKit', error_response, room=sid)

        @sio_app.event
        def messageToKit_kitReply(sid, data):
            """Handle messageToKit-kitReply - route UDA agent SDV-runtime responses back to test clients"""
            cmd = data.get('cmd', '')
            request_from = data.get('request_from', 'unknown')
            kit_id = data.get('kit_id', '')
            result = data.get('result', '')
            is_done = data.get('isDone', True)
            code = data.get('code', 0)

            print(f"📨 Received SDV runtime response '{cmd}' (kit: {kit_id[:15]}...)")
            print(f"   Request from: {request_from}")
            print(f"   Is Done: {is_done}, Code: {code}")

            # Find which kit sent this response
            kit_info = None
            for kid, info in registered_kits.items():
                if info['socket_id'] == sid:
                    kit_info = info
                    break

            if kit_info and 'active_request' in kit_info:
                # Route response back to original test client
                original_request = kit_info['active_request']
                test_client_sid = original_request['original_sid']

                print(f"🎯 Routing response back to test client: {test_client_sid}")
                sio_app.emit('messageToKit-kitReply', data, room=test_client_sid)

                # Clear active request if this is the final response
                if is_done:
                    kit_info.pop('active_request', None)
            else:
                print(f"⚠️ No active request found for kit {kit_id}, broadcasting to all clients")
                sio_app.emit('messageToKit-kitReply', data)

        @sio_app.on('*')
        def catch_all(event, sid, data):
            """Log all events for debugging"""
            if event not in ['connect', 'disconnect', 'messageToKit', 'messageToKit-kitReply', 'register_kit']:
                print(f"📨 Received event '{event}' from {sid}")
                if isinstance(data, dict) and len(str(data)) < 300:
                    print(f"📦 Data: {json.dumps(data, indent=2)}")

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