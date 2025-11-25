# UDA Testing Framework

## 🧪 Comprehensive Testing for Universal Deployment Agent

This testing framework provides complete validation of the UDA agent across different deployment modes and scenarios.

## 🎯 Test Coverage

### **Deployment Modes**
- ✅ **Docker Mode**: 3 test devices with containerized deployment
- ✅ **Non-Docker Mode**: 3 test devices with direct Python process deployment

### **Application Types**
- ✅ **Python Apps**: SDV Runtime compatible vehicle applications
- ✅ **Speed Monitor**: Vehicle speed monitoring with KUKSA integration
- ✅ **GPS Tracker**: GPS location tracking with navigation features

### **Integration Points**
- ✅ **Kit Server Adapter**: Protocol bridge connectivity and functionality
- ✅ **KUKSA Data Broker**: Vehicle signal exchange and VSS compatibility
- ✅ **Device Registration**: Automatic device discovery and registration
- ✅ **App Deployment**: Remote application deployment and lifecycle management
- ✅ **Signal Communication**: Real-time vehicle signal access

## 🚀 Quick Start

### **Prerequisites**
```bash
# Ensure UDA infrastructure is running
cd /path/to/uda-agent
./start-demo.sh

# Install test dependencies
pip install requests socketio asyncio
```

### **Run Complete Test Suite**
```bash
cd tests
python3 run_tests.py

# Or run directly
python3 test_framework.py
```

## 📋 Test Scenarios

### **Scenario 1: Docker Mode Testing**
```
🐳 Create 3 Docker containers
📱 Deploy UDA agent to each container
🔗 Test connection to Kit Server Adapter
📦 Deploy speed-monitor app to each device
📊 Verify Vehicle.Speed signals in KUKSA
📦 Deploy gps-tracker app to each device
🗺️ Verify GPS signals in KUKSA
🛑 Cleanup all containers
```

### **Scenario 2: Non-Docker Mode Testing**
```
🐍 Start 3 Python processes directly
📱 Deploy UDA agent to each process
🔗 Test connection to Kit Server Adapter
📦 Deploy speed-monitor app to each device
📊 Verify Vehicle.Speed signals in KUKSA
📦 Deploy gps-tracker app to each device
🗺️ Verify GPS signals in KUKSA
🛑 Cleanup all processes
```

### **Scenario 3: Mixed Mode Testing**
```
🐳 1 Docker container
🐍 2 Python processes
🔄 Test cross-mode compatibility
📊 Compare performance metrics
🛑 Clean up all resources
```

## 📊 Test Results

### **Pass/Fail Criteria**
- ✅ **Device Registration**: Device appears in Kit Server registry
- ✅ **App Deployment**: App deployment request succeeds
- ✅ **Signal Access**: App can read/write vehicle signals
- ✅ **Resource Usage**: Device stays within expected resource limits
- ✅ **Error Handling**: System handles failures gracefully

### **Performance Metrics**
- **Startup Time**: < 30 seconds per device
- **Memory Usage**: < 100MB per device (Docker mode), < 50MB (Non-Docker)
- **CPU Usage**: < 10% during normal operation
- **Network Latency**: < 100ms for Kit Server communication
- **KUKSA Signal Access**: < 50ms for signal get/set operations

## 🔍 Test Files Structure

```
tests/
├── test_framework.py      # Main testing framework
├── run_tests.py          # Simple test runner
├── README.md             # This file
├── test_report.md        # Generated test reports
├── unit/                 # Unit tests
│   └── test_agent.py    # Agent functionality tests
├── integration/          # Integration tests
│   └── test_kit_server.py # Kit Server integration
├── fixtures/            # Test data and mock services
│   ├── test_apps/       # Test applications
│   └── mock_services/  # Mock services for testing
└── simulators/          # Device simulators
    ├── docker_sim.py  # Docker device simulator
    └── process_sim.py  # Process device simulator
```

## 📈 Test Reports

### **Generated Reports**
- **test_report.md**: Comprehensive test report with pass/fail statistics
- **Detailed Logs**: Per-device logs with timestamps
- **Performance Metrics**: Resource usage and timing information
- **Error Analysis**: Detailed error messages and stack traces

### **Report Sections**
- Executive Summary
- Test Coverage Matrix
- Deployment Mode Results
- Device-Specific Results
- Performance Benchmarks
- Issues and Recommendations

## 🛠️ Customization

### **Adding New Test Scenarios**
```python
# In test_framework.py
async def custom_test_scenario(self):
    """Custom test scenario"""
    # Create custom test devices
    devices = self.create_test_devices('custom', count=5)

    # Run custom test logic
    for device in devices:
        # Custom test steps
        pass
```

### **Adding New Test Applications**
```python
# In main test function
test_apps = {
    'custom-app': load_app_from_file('custom_app.py'),
    'another-app': load_app_from_file('another_app.py')
}
```

### **Custom Performance Thresholds**
```python
# Adjust in test_framework.py
STARTUP_TIMEOUT = 30  # seconds
MEMORY_LIMIT = 100   # MB
CPU_LIMIT = 10       # %
```

## 🔧 Environment Variables

### **Test Configuration**
```bash
export KIT_SERVER_URL="http://localhost:3090"
export KUKSA_URL="http://localhost:55555"
export DEVICE_COUNT=3
export TEST_TIMEOUT=300
export LOG_LEVEL=INFO
```

### **Docker Configuration**
```bash
export DOCKER_REGISTRY="localhost:5000"
export DOCKER_TAG_PREFIX="uda-test"
export CONTAINER_NETWORK="dreamkit-network"
```

## 🐛 Troubleshooting

### **Common Issues**

**1. Kit Server Not Running**
```
Error: Cannot connect to Kit Server Adapter
Solution: Run ./start-demo.sh first
```

**2. Docker Network Issues**
```
Error: Container network not found
Solution: Ensure dreamkit-network exists
```

**3. Permission Issues**
```
Error: Permission denied
Solution: Run with appropriate user permissions
```

**4. Port Conflicts**
```
Error: Port already in use
Solution: Stop conflicting services
```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 test_framework.py
```

### **Cleanup**
```python
# Force cleanup of all test resources
python3 -c "
from test_framework import UDATestFramework
framework = UDATestFramework()
for device in framework.devices.values():
    framework.stop_device(device)
"
```

## 📝 Test Guidelines

### **Before Running Tests**
1. Ensure all infrastructure components are running
2. Verify network connectivity
3. Check available system resources
4. Clear any previous test artifacts

### **During Tests**
1. Monitor system resource usage
2. Watch for unexpected errors
3. Log all test activities
4. Check device connectivity

### **After Tests**
1. Review test report for issues
2. Clean up test resources
3. Archive test results
4. Update documentation

## 🎯 Success Criteria

### **Minimum Requirements**
- All devices register successfully
- All apps deploy without errors
- All vehicle signals are accessible
- No resource leaks detected
- Clean shutdown of all resources

### **Optimal Performance**
- Startup time under 20 seconds per device
- Memory usage under 50MB per device
- CPU usage under 5% during normal operation
- Network latency under 50ms for local connections

**This testing framework ensures comprehensive validation of the UDA agent across all supported deployment modes and use cases!**