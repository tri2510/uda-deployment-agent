#!/usr/bin/env python3
"""
Simple Mock Kit Server for testing UDA agent
"""

import socketio
import threading
import time
import json
from datetime import datetime

sio = socketio.Server(cors_allowed_origins="*", logger=False, engineio_logger=False)

# Storage
connected_clients = {}
registered_kits = {}

print("🧪 Simple Flask-SocketIO Mock Kit Server")
print("=" * 50)

@sio.event
def connect(sid, environ):
    print(f"🔌 Client connected: {sid}")
    connected_clients[sid] = {
        'connected_at': datetime.now().isoformat(),
        'sid': sid
    }

@sio.event
def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")
    if sid in connected_clients:
        del connected_clients[sid]

    # Mark kit as offline if it was registered
    for kit_id, kit_info in list(registered_kits.items()):
        if kit_info.get('socket_id') == sid:
            kit_info['is_online'] = False
            print(f"📡 Kit went offline: {kit_id}")

@sio.event
def register_kit(sid, data):
    """Handle kit registration"""
    kit_id = data.get('kit_id')
    name = data.get('name')
    kit_type = data.get('type', 'unknown')

    print(f"🏷️  Kit registered: {kit_id} ({name})")

    # Store kit info
    registered_kits[kit_id] = {
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
    sio.emit('register_kit_ack', {
        'kit_id': kit_id,
        'status': 'registered',
        'message': f'Kit {kit_id} registered successfully'
    }, room=sid)

@sio.event
def messageToKit(sid, data):
    """Handle messageToKit - route requests and responses"""
    cmd = data.get('cmd', '')
    target_kit_id = data.get('to_kit_id', '')
    request_from = data.get('request_from', 'unknown')

    print(f"📨 Received messageToKit: cmd='{cmd}', kit='{target_kit_id}', from='{request_from}'")

    # Determine if this is a request from test client or response from UDA agent
    is_response = ('result' in data) or data.get('is_finish', False) or data.get('isDone', False)

    if is_response:
        # This is a response from UDA agent - route it back to the original test client
        print(f"📨 Response from UDA agent: {cmd}")

        # Find which kit sent this response
        kit_id = None
        kit_info = None
        for kid, info in registered_kits.items():
            if info['socket_id'] == sid:
                kit_id = kid
                kit_info = info
                break

        if kit_id and kit_info and 'active_request' in kit_info:
            original_sid = kit_info['active_request']['original_sid']
            original_cmd = kit_info['active_request']['cmd']

            if cmd == original_cmd:
                print(f"🎯 Routing response from UDA agent '{kit_id}' back to test client")
                print(f"📦 Response: {json.dumps(data, indent=2)}")

                # Send response back to original test client
                sio.emit('messageToKit', data, room=original_sid)

                # Clear active request
                del kit_info['active_request']
            else:
                print(f"⚠️ Response command mismatch: expected {original_cmd}, got {cmd}")
        else:
            print(f"⚠️ Received response but no active request found for kit {kit_id}")
    else:
        # This is a request from test client - forward it to UDA agent
        print(f"📨 Request from test client: {cmd} for kit {target_kit_id}")

        # Find the target kit
        if target_kit_id in registered_kits:
            kit_info = registered_kits[target_kit_id]
            target_sid = kit_info['socket_id']

            print(f"🎯 Forwarding request to kit: {target_kit_id} (sid: {target_sid})")

            # Forward the message to the target kit
            sio.emit('messageToKit', data, room=target_sid)

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
            sio.emit('messageToKit', error_response, room=sid)

@sio.event
def messageToKit_kitReply(sid, data):
    """Handle messageToKit-kitReply - route UDA agent SDV-runtime responses back to test clients"""
    cmd = data.get('cmd', '')
    request_from = data.get('request_from', 'unknown')
    kit_id = data.get('kit_id', '')
    result = data.get('result', '')
    is_done = data.get('isDone', True)
    code = data.get('code', 0)

    print(f"📨 RECEIVED messageToKit-kitReply: {cmd} (kit: {kit_id[:15]}...)")
    print(f"   Request from: {request_from}")
    print(f"   Is Done: {is_done}, Code: {code}")
    print(f"   Result: {result[:100]}{'...' if len(result) > 100 else ''}")

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

        print(f"🎯 Routing messageToKit-kitReply response back to test client: {test_client_sid}")
        sio.emit('messageToKit-kitReply', data, room=test_client_sid)

        # Clear active request if this is the final response
        if is_done:
            kit_info.pop('active_request', None)
    else:
        print(f"⚠️ No active request found for kit {kit_id}, broadcasting to all clients")
        sio.emit('messageToKit-kitReply', data, broadcast=True)

@sio.on('*')
def catch_all(event, sid, data):
    """Log all events for debugging"""
    if event not in ['connect', 'disconnect', 'messageToKit', 'messageToKit-kitReply', 'register_kit']:
        print(f"📨 Received event '{event}' from {sid}")
        if isinstance(data, dict) and len(str(data)) < 300:
            print(f"📦 Data: {json.dumps(data, indent=2)}")

def status_monitor():
    """Print status every 15 seconds"""
    while True:
        time.sleep(15)
        print(f"\n📊 Server Status:")
        print(f"   Connected clients: {len(connected_clients)}")
        print(f"   Registered kits: {len(registered_kits)}")

        if registered_kits:
            for kit_id, kit_info in registered_kits.items():
                status = "🟢 Online" if kit_info['is_online'] else "🔴 Offline"
                print(f"   • {kit_id} - {status}")

if __name__ == "__main__":
    # Start status monitoring thread
    status_thread = threading.Thread(target=status_monitor, daemon=True)
    status_thread.start()

    print("🚀 Starting Simple Mock Kit Server on port 3091")
    print("📡 Server will be available at: http://localhost:3091")
    print("=" * 50)

    # Create a simple WSGI application and wrap with Socket.IO
    def simple_wsgi_app(environ, start_response):
        """Simple WSGI app that returns 404 for HTTP requests"""
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'Not Found - This is a Socket.IO server only']

    # Wrap with Socket.IO WSGI app
    app = socketio.WSGIApp(sio, simple_wsgi_app)

    # Start server with eventlet
    try:
        import eventlet
        eventlet.wsgi.server(eventlet.listen(('', 3091)), app)
    except ImportError:
        print("⚠️ eventlet not available, using wsgiref")
        from wsgiref.simple_server import make_server
        httpd = make_server('', 3091, app)
        print(f"🌐 Starting server with wsgiref on port 3091")
        httpd.serve_forever()