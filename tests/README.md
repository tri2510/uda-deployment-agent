# UDA Agent Kit Server Message Tests

This directory contains test scripts to simulate Kit Server messages and test the UDA agent's SDV runtime compatibility.

## 🎯 Target Runtime

- **Runtime Name**: `UDA-5dc4bfa4`
- **Kit ID**: `Runtime-UDA-5dc4bfa4`
- **Agent URL**: `http://localhost:3090`
- **Kit Server**: `https://kit.digitalauto.tech`

## 📋 Test Files

### 1. **test_connectivity.py**
Tests basic connectivity to the UDA agent.
```bash
python3 test_connectivity.py
```

### 2. **test_runtime_info.py**
Tests the `get-runtime-info` command to get runtime status and running apps.
```bash
python3 test_runtime_info.py
```

### 3. **test_deploy_request.py**
Tests the `deploy_request` command to deploy a Python application.
```bash
python3 test_deploy_request.py
```

### 4. **test_run_python_app.py**
Tests the `run_python_app` command for direct Python execution.
```bash
python3 test_run_python_app.py
```

### 5. **test_stop_python_app.py**
Tests the `stop_python_app` command to stop running applications.
```bash
python3 test_stop_python_app.py
```

### 6. **test_output_to_kitserver.py**
Tests UDA agent's ability to send output messages back to Kit Server.
```bash
python3 test_output_to_kitserver.py
```

### 7. **run_tests.py**
Runs all tests in sequence.
```bash
python3 run_tests.py
```

## 🚀 Usage

### Step 1: Start UDA Agent
```bash
cd /home/htr1hc/01_SDV/73_autowrx_v3/autowrx-sdv-rnd/uda-agent
python3 src/uda_agent.py
```

### Step 2: Test Connectivity
```bash
cd tests
python3 test_connectivity.py
```

### Step 3: Run Individual Tests
```bash
# Test runtime info
python3 test_runtime_info.py

# Deploy a simple Python app
python3 test_deploy_request.py

# Run Python app directly
python3 test_run_python_app.py

# Stop running app
python3 test_stop_python_app.py
```

### Step 4: Run All Tests
```bash
python3 run_tests.py
```

## 📨 Message Format

The tests send messages in SDV runtime format:

```json
{
  "cmd": "deploy_request | run_python_app | stop_python_app | get-runtime-info",
  "request_from": "test-client-xxx",
  "to_kit_id": "Runtime-UDA-5dc4bfa4",
  "name": "app-name",
  "code": "python code here",
  "prototype": {"name": "AppClassName"}
}
```

## 📤 Expected Response Format

```json
{
  "request_from": "test-client-xxx",
  "cmd": "command-name",
  "result": "result message",
  "is_finish": true,
  "code": 0,
  "isDone": true
}
```

## 🔍 What Each Test Does

### Runtime Info Test
- Sends `get-runtime-info` command
- Expects runtime status, running apps list
- Shows runtime name and capabilities

### Deploy Request Test
- Sends `deploy_request` command with simple Python code
- Deploys app that runs for ~10 seconds
- Logs deployment status and app output

### Run Python App Test
- Sends `run_python_app` command with time-based code
- Executes Python app directly without deployment
- Shows immediate execution and output

### Stop Python App Test
- Sends `stop_python_app` command
- Stops previously deployed app
- Shows graceful shutdown

### Output Messages to Kit Server Test
- Sends `run_python_app` command with output-generating code
- Tests UDA agent's ability to send various types of messages back to Kit Server
- Verifies bidirectional communication including:
  - Status updates during execution
  - Log messages and output
  - Execution results and error messages
  - Real-time streaming capabilities

## 🐛 Troubleshooting

### UDA Agent Not Running
```bash
# Start the agent first
python3 ../src/uda_agent.py

# The agent should show:
# ✅ Runtime 'UDA-5dc4bfa4' is now online and discoverable
```

### Connection Refused
```bash
# Check if agent is listening
netstat -an | grep 3090

# Or test connectivity
python3 test_connectivity.py
```

### Tests Time Out
- Make sure agent is running and connected to Kit Server
- Check network connectivity to localhost:3090
- Review agent logs for any errors

## 📝 Notes

- Tests simulate Kit Server messages using Socket.IO client
- Each test connects independently and disconnects after completion
- Apps are deployed to `./deployments/` directory with logs in `./logs/`
- Runtime name persists across agent restarts via `.runtime_name` file
- All tests target the specific runtime: `Runtime-UDA-5dc4bfa4`