# 🧪 UDA Testing Guide

## 📋 Complete Automated Testing for Universal Deployment Agent

This guide explains how to use the comprehensive automated testing framework for the UDA (Universal Deployment Agent).

## 🚀 Quick Start

### **Run Quick Tests (Isolated Mode)**
```bash
# Run isolated tests (recommended for quick validation)
./run_uda_tests.sh

# OR explicitly:
./run_uda_tests.sh --isolated
```

### **Run Full Comprehensive Tests**
```bash
# Run complete test suite with Docker and performance analysis
./run_uda_tests.sh --comprehensive
```

### **Check Dependencies Only**
```bash
# Verify system dependencies before running tests
./run_uda_tests.sh --dependencies
```

## 📊 Test Coverage

### **✅ What Gets Tested**

#### **Isolated Mode Tests**
- **3 UDA Devices**: Simulated devices connecting via Socket.IO
- **6 App Deployments**: 2 apps per device (speed-monitor, gps-tracker)
- **Mock Kit Server**: Complete protocol bridge simulation
- **Communication**: UDA ↔ Kit Server ↔ App deployment

#### **Comprehensive Mode Tests**
- **Non-Docker Mode**: Direct Python process deployment
- **Docker Mode**: Containerized UDA deployment (when available)
- **Performance Analysis**: CPU, memory, network latency measurements
- **System Monitoring**: Resource usage and scalability testing

#### **App Types Tested**
- **Speed Monitor**: Vehicle speed monitoring simulation
- **GPS Tracker**: GPS location tracking simulation
- **Both Apps**: Deployed to all devices in both modes

## 📁 Generated Reports

After running tests, you'll get detailed reports in the `tests/` directory:

### **📄 test_output.log**
- Detailed execution log with timestamps
- Complete trace of all test operations
- Error messages and debugging information

### **📊 test_report.html** (Comprehensive Mode)
- Interactive HTML report with charts and tables
- Executive summary with pass/fail status
- Detailed performance metrics
- Device and deployment breakdown

### **📋 test_report.json** (Comprehensive Mode)
- Raw JSON data for programmatic analysis
- Complete test results in machine-readable format
- Integration with CI/CD pipelines

## 🔧 Test Options

### **Command Line Options**

| Option | Description | Example |
|--------|-------------|---------|
| `-h, --help` | Show help message | `./run_uda_tests.sh --help` |
| `-i, --isolated` | Run isolated tests only | `./run_uda_tests.sh --isolated` |
| `-c, --comprehensive` | Run full test suite | `./run_uda_tests.sh --comprehensive` |
| `-d, --dependencies` | Check dependencies only | `./run_uda_tests.sh --dependencies` |
| `-r, --reports` | Generate summary reports | `./run_uda_tests.sh --reports` |
| `-v, --verbose` | Enable verbose output | `./run_uda_tests.sh --verbose` |

### **Environment Variables**

You can customize test behavior with these environment variables:

```bash
# Set custom Kit Server URL
export KIT_SERVER_URL="http://localhost:3090"

# Set device count for testing
export DEVICE_COUNT=3

# Enable debug logging
export LOG_LEVEL=DEBUG
```

## 📈 Understanding Test Results

### **Success Criteria**

#### **Isolated Mode**
- ✅ **3 devices registered and connected**
- ✅ **6 apps deployed successfully** (2 per device)
- ✅ **UDA communication working**
- ✅ **Mock Kit Server functioning**

#### **Comprehensive Mode**
- All isolated mode criteria PLUS:
- ✅ **Docker containers running** (if Docker available)
- ✅ **Performance metrics collected**
- ✅ **Resource usage within limits**

### **Performance Metrics**

#### **Key Metrics Tracked**
- **Startup Time**: Time to connect each device
- **CPU Usage**: Processor utilization during tests
- **Memory Usage**: Memory consumption patterns
- **Network Latency**: Communication delays
- **Deployment Time**: Time to deploy each app

#### **Performance Thresholds**
- **Device Startup**: < 5 seconds per device
- **App Deployment**: < 2 seconds per app
- **Network Latency**: < 50ms average
- **Memory Usage**: < 100MB per UDA instance

### **Report Sections**

#### **Console Output**
```
🚀 UDA Comprehensive Test Runner
============================================================
🔍 Checking Dependencies
✅ Python 3: Python 3.10.12
✅ Docker: Running and accessible
✅ All dependencies satisfied

🧪 Running Isolated UDA Tests
✅ Isolated tests completed successfully

📊 Test Summary Report
✅ Overall Test Status: PASSED
✅ Successful operations: 17
❌ Errors: 0
```

#### **HTML Report Features**
- **Executive Summary**: Overall pass/fail status
- **Test Coverage Matrix**: Which tests were run
- **Performance Charts**: Resource usage over time
- **Device Details**: Per-device performance metrics
- **Deployment Tracking**: App deployment success rates

## 🛠️ Troubleshooting

### **Common Issues**

#### **Docker Tests Skipped**
```bash
# Check if Docker is running
sudo systemctl status docker

# Start Docker service
sudo systemctl start docker
```

#### **Python Package Errors**
```bash
# Install required packages
pip3 install aiohttp psutil docker requests python-socketio

# Verify installation
python3 -c "import aiohttp, psutil, docker, requests, socketio"
```

#### **Port Conflicts**
```bash
# Check if port 3090 is in use
netstat -tulpn | grep 3090

# Kill conflicting processes
pkill -f "mock_kit_server.py"
```

#### **UDA Agent Not Found**
```bash
# Check if UDA agent exists
ls -la uda-agent.py

# Make sure you're in the right directory
pwd  # Should be .../uda-agent
```

### **Debug Mode**

#### **Enable Verbose Logging**
```bash
# Run with verbose output
./run_uda_tests.sh --verbose

# Check detailed logs
tail -f tests/test_output.log
```

#### **Manual Test Components**
```bash
# Start mock Kit Server manually
python3 tests/mock_kit_server.py

# Test UDA agent manually
KIT_SERVER_URL=http://localhost:3090 python3 uda-agent.py
```

## 🔧 Advanced Usage

### **Custom Test Scenarios**

You can modify the test files to create custom scenarios:

#### **Modify Device Count**
```python
# In tests/isolated_test_runner.py
non_docker_devices = ['device-1', 'device-2', 'device-3', 'device-4', 'device-5']
```

#### **Add Custom Apps**
```python
# In test runners, modify app_configs
app_configs = {
    'custom-app': {
        'app_name': 'custom-app',
        'type': 'python',
        'code': 'print("Custom app running")',
        'execution_mode': 'background'
    }
}
```

### **Integration with CI/CD**

#### **GitHub Actions Example**
```yaml
name: UDA Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run UDA Tests
      run: |
        chmod +x run_uda_tests.sh
        ./run_uda_tests.sh --isolated
    - name: Upload Test Reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: tests/
```

## 📚 Test Architecture

### **Component Overview**

```
run_uda_tests.sh              # Main shell script
├── comprehensive_test_runner.py # Full test suite with Docker/performance
├── isolated_test_runner.py      # Quick isolated tests
├── mock_kit_server.py          # Simulated Kit Server
├── test_framework.py           # Original comprehensive framework
└── uda-agent.py  # UDA being tested
```

### **Test Flow**

1. **Dependency Check**: Verify Python, Docker, packages
2. **Environment Setup**: Clean previous processes, prepare logs
3. **Mock Server Start**: Launch simulated Kit Server on port 3090
4. **Device Simulation**: Start 3 UDA agents
5. **App Deployment**: Deploy speed-monitor and gps-tracker apps
6. **Performance Analysis**: Measure resource usage and latency
7. **Report Generation**: Create HTML, JSON, and console reports
8. **Cleanup**: Stop all processes and containers

### **Communication Flow**

```
UDA Agent (3 instances)
    ↓ Socket.IO (Port 3090)
Mock Kit Server
    ↓ HTTP REST API
Test Runner
    ← Performance Metrics
    ← Test Results
```

## 🎯 Best Practices

### **Before Running Tests**
1. **Check Dependencies**: Run `./run_uda_tests.sh --dependencies`
2. **Clean Environment**: Remove conflicting processes
3. **Verify Network**: Ensure port 3090 is available
4. **Check Disk Space**: Tests generate log files and reports

### **During Tests**
1. **Monitor Output**: Watch for error messages
2. **Check Resources**: Monitor CPU and memory usage
3. **Verify Connections**: Ensure devices connect properly
4. **Track Progress**: Use progress indicators in shell script

### **After Tests**
1. **Review Reports**: Check HTML and JSON reports
2. **Analyze Logs**: Look for warnings or errors
3. **Validate Results**: Ensure all criteria met
4. **Archive Results**: Save reports for historical comparison

## 🔗 Integration Points

### **With Existing Infrastructure**
- **Kit Server Adapter**: Works as drop-in replacement
- **KUKSA Data Broker**: Compatible with existing deployments
- **Docker Networks**: Uses standard Docker networking
- **Socket.IO Protocol**: Compatible with existing UDA implementations

### **With Development Workflow**
- **Local Development**: Quick validation during development
- **CI/CD Integration**: Automated testing in pipelines
- **Performance Regression**: Track performance over time
- **Documentation**: Generated reports for compliance

---

**🎉 Your UDA testing framework is now fully automated!**

Run `./run_uda_tests.sh` to start testing, and check the `tests/` directory for detailed reports.