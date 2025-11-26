# UDA Agent SDV Runtime Compatibility Tests

This directory contains a comprehensive test suite for verifying the Universal Deployment Agent's (UDA) SDV runtime compatibility and Kit Server integration capabilities.

## 🏗️ Test Organization

The test suite is organized into four distinct categories:

### 📋 Unit Tests (`unit/`)
Basic functionality and connectivity tests.
- **`test_connectivity.py`** - Tests basic connection between UDA agent and test clients
- **`debug_routing.py`** - Debugging tool for message routing verification

### 🔗 Integration Tests (`integration/`)
Core SDV runtime feature tests that validate individual functionality.
- **`test_runtime_info.py`** - Tests `get-runtime-info` command and runtime status retrieval
- **`test_deploy_request.py`** - Tests `deploy_request` command for Python app deployment
- **`test_run_python_app.py`** - Tests `run_python_app` command for direct execution
- **`test_stop_python_app.py`** - Tests `stop_python_app` command for app termination
- **`test_output_to_kitserver.py`** - Tests real-time output streaming to Kit Server

### 🔄 Regression Tests (`regression/`)
Critical functionality tests that ensure SDV runtime compatibility is maintained.
- **`test_messageTokit_kitReply.py`** - Verifies proper `messageToKit-kitReply` event emission

### 🎯 End-to-End Tests (`e2e/`)
Complete workflow and scenario tests that validate the entire system.
- **`test_full_flow.py`** - Tests complete Mock Kit Server → UDA Agent → Test Client flow

### 🛠️ Test Tools (`tools/`)
Supporting tools and mock servers for test execution.
- **`mock_kit_server.py`** - Flask-SocketIO Mock Kit Server for SDV runtime simulation
- **`simple_mock_server.py`** - Simplified mock server for debugging

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with pip
- UDA agent source code at `../src/uda_agent.py`
- Required packages: `socketio`, `flask-socketio`, `python-socketio`

### Running All Tests
```bash
# Run complete test suite
python3 run_tests.py

# Run in fast mode (limited tests for quick validation)
python3 run_tests.py --fast

# Run specific test category
python3 run_tests.py --category integration
python3 run_tests.py --category regression
python3 run_tests.py --category e2e
```

### Running Individual Tests
```bash
# Unit tests
python3 unit/test_connectivity.py

# Integration tests
python3 integration/test_runtime_info.py
python3 integration/test_deploy_request.py

# End-to-end tests
python3 e2e/test_full_flow.py
```

### Test with Mock Server
Most tests automatically start and stop the Mock Kit Server. For manual testing:

```bash
# Start mock server
python3 tools/mock_kit_server.py

# In another terminal, run UDA agent
cd ..
python3 src/uda_agent.py --server http://localhost:3091

# Run tests
cd tests
python3 integration/test_runtime_info.py
```

## 📊 Test Results

After running tests, a detailed report is generated with:
- Test execution summary
- Pass/fail status per test suite
- Overall success rate
- Timestamped report file saved

Example report:
```
🎯 Overall: 10/10 tests passed (100.0%)
🎉 All tests passed! UDA agent is ready for production.
```

## 🎯 Target Runtime

All tests target the SDV runtime configuration:
- **Runtime Name**: `UDA-5dc4bfa4`
- **Kit ID**: `Runtime-UDA-5dc4bfa4`
- **Agent URL**: `http://localhost:3091`
- **Mock Kit Server**: `http://localhost:3091`

## 📨 Message Format Tests

The tests validate SDV runtime compatible message formats:

### Client → Kit Server Requests
```json
{
  "cmd": "get-runtime-info | deploy_request | run_python_app | stop_python_app",
  "request_from": "test-client-xxx",
  "to_kit_id": "Runtime-UDA-5dc4bfa4",
  "name": "app-name",
  "code": "python code here",
  "prototype": {"name": "AppClassName"}
}
```

### Kit Server → Client Responses
```json
{
  "kit_id": "Runtime-UDA-5dc4bfa4",
  "request_from": "test-client-xxx",
  "cmd": "command-name",
  "result": "Success or error message",
  "isDone": true,
  "code": 0
}
```

## 🔍 SDV Runtime Compatibility

The UDA agent implements full SDV runtime compatibility:

### ✅ Core Features Validated
- **messageToKit-kitReply events** with proper Kit Server format
- **Real-time stdout streaming** via `app_output` events
- **Deployment status updates** during app deployment process
- **App lifecycle status** for start/stop/terminate events
- **Runtime state reporting** for kit status monitoring

### ✅ Message Protocol Compliance
- Proper event naming (`messageToKit-kitReply`)
- Required fields included (`kit_id`, `request_from`, `cmd`, `isDone`, `code`)
- SDV runtime data structure compatibility
- Error handling and response codes

### ✅ Real-time Features
- Continuous stdout streaming with proper event emission
- Deployment progress reporting with percentage completion
- App status changes (starting, running, stopped, error)
- Runtime state broadcasting every 5 seconds

## 🐛 Troubleshooting

### Common Issues

#### UDA Agent Not Running
```bash
# Start the agent first
cd ..
python3 src/uda_agent.py --server http://localhost:3091

# Agent should show:
# ✅ Runtime 'UDA-5dc4bfa4' is now online and discoverable
```

#### Connection Refused
```bash
# Check if agent is listening
netstat -an | grep 3091

# Test connectivity
python3 unit/test_connectivity.py
```

#### Tests Time Out
- Ensure Mock Kit Server is running
- Check network connectivity to localhost:3091
- Review UDA agent logs for connection errors
- Verify no port conflicts exist

#### Import Errors
```bash
# Install required packages
pip install python-socketio flask-socketio

# Check Python path
python3 -c "import socketio; print('✅ Socket.IO available')"
```

### Debug Mode

For detailed debugging, use the debug routing test:
```bash
python3 unit/debug_routing.py
```

This provides detailed logging of:
- Mock Kit Server event handling
- Message routing verification
- UDA agent event registration
- Socket.IO communication flow

## 📝 Test Development

### Adding New Tests

1. **Choose category** based on test scope:
   - `unit/` - Single component tests
   - `integration/` - Feature tests
   - `regression/` - Critical functionality
   - `e2e/` - Complete workflows

2. **Follow naming convention**:
   - `test_<feature>_<scenario>.py`
   - Descriptive test names

3. **Include auto-setup**:
   ```python
   def check_mock_server_running():
       # Check if mock server is available
       pass

   def check_uda_agent_running():
       # Check if UDA agent is running
       pass

   def start_mock_server():
       # Auto-start mock server
       pass

   def start_uda_agent():
       # Auto-start UDA agent
       pass
   ```

4. **Use proper event handling**:
   ```python
   @sio.event
   def messageToKit_kitReply(sid, data):
       # Handle SDV runtime responses
       pass

   @sio.on('*')
   def catch_all(event, data):
       # Log all events for debugging
       pass
   ```

## 🔄 Continuous Integration

The test suite is designed for CI/CD integration:

### Test Categories for CI
- **Fast Mode** (`--fast`): Essential tests for quick validation
- **Unit Tests**: Component-level testing
- **Integration Tests**: Feature validation
- **Regression Tests**: Critical functionality checks

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed
- `2`: Test setup errors

### CI Example
```bash
# Fast validation
python3 run_tests.py --fast

# Full test suite
python3 run_tests.py

# Specific category
python3 run_tests.py --category regression
```

## 📈 Test Coverage

The test suite validates:

### ✅ Connectivity
- Socket.IO client connections
- Mock Kit Server availability
- UDA agent registration
- Event handler registration

### ✅ SDV Runtime Commands
- `get-runtime-info` - Runtime status and app list
- `deploy_request` - App deployment with status tracking
- `run_python_app` - Direct Python execution
- `stop_python_app` - App termination

### ✅ Real-time Features
- Continuous stdout streaming
- Deployment progress updates
- App lifecycle status changes
- Runtime state reporting

### ✅ Error Handling
- Invalid command responses
- Missing field handling
- Connection failure recovery
- Timeout management

### ✅ Message Protocol
- Proper event naming
- Required field validation
- Response format compliance
- SDV runtime specification adherence

## 🎯 Production Readiness

All tests passing indicates that the UDA agent is:
- ✅ **SDV runtime compatible** with full Kit Server integration
- ✅ **Production ready** with comprehensive validation
- ✅ **Real-time capable** with stdout streaming support
- ✅ **Protocol compliant** with SDV runtime specifications

The UDA agent can now be confidently deployed in SDV runtime environments with Kit Server compatibility.