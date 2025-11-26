# Universal Deployment Agent (UDA)

SDV Runtime compatible Python deployment agent for vehicle applications that connects to Kit Server Adapter and executes Python vehicle apps on KUKSA Data Broker using official Velocitas SDK patterns.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/tri2510/uda-deployment-agent.git
cd uda-deployment-agent

# Install dependencies
pip install -r config/requirements.txt

# Run the UDA agent
python3 src/uda_agent.py
```

## 📁 Project Structure

```
uda/
├── src/                    # Core UDA source code
│   └── uda_agent.py       # Main UDA agent
├── apps/                   # Vehicle applications
│   └── examples/          # Example apps
│       ├── speed_monitor.py
│       └── gps_tracker.py
├── config/                 # Configuration files
│   ├── requirements.txt
│   └── docker/            # Docker configuration
│       └── Dockerfile
├── scripts/                # Utility scripts
│   ├── start_demo.sh
│   └── docker_build.sh
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   └── guides/
```

## 🎯 Features

- **SDV Runtime Compatible**: Full Velocitas SDK integration
- **KUKSA Data Broker**: Real vehicle signal access
- **Socket.IO Communication**: Kit Server Adapter integration
- **Multi-Platform**: Linux, Docker, Yocto, baremetal support
- **Flexible Deployment**: Multiple agents per server
- **Real-time Management**: App deployment and monitoring

## 📦 Installation

### Requirements
- Python 3.7+
- Access to Kit Server Adapter
- KUKSA Data Broker running

### Basic Setup
```bash
# Install dependencies
pip install -r config/requirements.txt

# Run the UDA agent
python3 src/uda_agent.py --server http://localhost:3090
```

## 🐳 Docker Setup

```bash
# Build UDA image
cd config/docker
docker build -t uda-agent:latest .

# Run with KUKSA Data Broker
docker run -d \
  --name uda-agent \
  -e KIT_SERVER_URL=http://kit-server:3090 \
  -e KUKSA_DATA_BROKER_ADDRESS=kuksa-databroker:55555 \
  uda-agent:latest
```

## 🔧 Usage

### Start the Agent
```bash
# Basic usage
python3 src/uda_agent.py

# With custom server
python3 src/uda_agent.py --server http://localhost:3090

# With custom directories
python3 src/uda_agent.py \
  --deployment-dir ./deployments \
  --log-dir ./logs
```

### Deploy Vehicle Apps
Apps are deployed via Kit Server Adapter:

```json
{
  "app_name": "speed-monitor",
  "type": "python",
  "code": "# Your Python app code here",
  "execution_mode": "background"
}
```

## 🚗 Example Applications

### Speed Monitor
```bash
# Deploy speed monitoring app
# File: apps/examples/speed_monitor.py
```

### GPS Tracker
```bash
# Deploy GPS tracking app
# File: apps/examples/gps_tracker.py
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/api/) - API documentation (coming soon)

## 🔧 Configuration

### Environment Variables
- `KIT_SERVER_URL`: Kit Server Adapter URL (default: http://localhost:3090)
- `KUKSA_DATA_BROKER_ADDRESS`: KUKSA Data Broker address (default: localhost:55555)
- `SDV_MODE`: SDV mode (default: standard)
- `LOG_LEVEL`: Logging level (default: INFO)

### Agent Capabilities
The UDA agent automatically detects and advertises:
- Python app execution
- Velocitas SDK support
- KUKSA Data Broker integration
- Docker availability (if detected)

## 🚨 Security Considerations

### Current Limitations
- No app sandboxing
- Basic authentication via Kit Server
- No code validation

### Recommendations
- Run in isolated environment
- Use network segmentation
- Monitor deployed applications
- Regular security updates

## 📊 Performance

### Resource Usage
- **Memory**: ~50MB per agent
- **CPU**: <5% idle, <10% during app execution
- **Startup**: ~4 seconds
- **Network**: ~1.5ms latency to Kit Server

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add new functionality
4. Verify with demo scripts
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/tri2510/uda-deployment-agent/issues)
- **Documentation**: [docs/](./docs/)
- **Examples**: [apps/examples/](./apps/examples/)