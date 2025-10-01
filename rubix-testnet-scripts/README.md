# Rubix Testnet Node Management

Production-ready automation toolkit for managing Rubix blockchain testnet nodes with flexible configuration, robust error handling, and state management.

## ✨ Features

- **Flexible Configuration** - YAML-based configuration for easy customization
- **Multi-Platform Support** - Works on Linux, macOS (Intel & ARM), and Windows
- **State Management** - Resume from failures, track node status
- **Secure Password Management** - Environment variables or secure prompts
- **Health Checking** - Automatic retry with exponential backoff
- **Comprehensive Logging** - Detailed logs for debugging and monitoring
- **Idempotent Operations** - Safe to re-run without duplication

## 🚀 Quick Start

### Prerequisites

#### Required on All Platforms:
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Make** - For building rubixgoplatform

#### Platform-Specific Requirements:

**macOS:**
- **tmux** - Required for running nodes in background
  ```bash
  brew install tmux
  ```
- **Xcode Command Line Tools** - For Make
  ```bash
  xcode-select --install
  ```

**Linux (Ubuntu/Debian):**
- **tmux** - Required for running nodes in background
  ```bash
  sudo apt-get update
  sudo apt-get install tmux build-essential
  ```

**Windows:**
- **PowerShell** - Built-in (no installation needed)
- **Make** - Install via [Chocolatey](https://chocolatey.org/)
  ```powershell
  choco install make
  ```

### Installation

1. **Clone and navigate to directory**
   ```bash
   cd rubix-testnet-scripts
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure (optional)**
   ```bash
   # Edit config.yaml to customize node counts, ports, etc.
   vim config.yaml
   ```

4. **Setup environment variables (optional)**
   ```bash
   # Copy example and edit
   cp .env.example .env
   vim .env

   # Load environment
   source .env
   ```

5. **Run setup**
   ```bash
   python setup.py
   ```

## 📖 Usage

### Setup Nodes (First Time)

```bash
# Use default configuration (5 quorum + 2 non-quorum nodes)
python setup.py

# With custom configuration
python setup.py --config custom-config.yaml

# Force reinstall everything
python setup.py --force

# Clean start (remove all data)
python setup.py --clean

# Enable debug logging
python setup.py --log-level DEBUG
```

### Stop Nodes

```bash
# Stop all nodes
python stop.py

# Stop specific node
python stop.py --node 3

# Stop range of nodes
python stop.py --start 0 --end 4
```

### Restart Nodes

```bash
# Restart all nodes
python restart_nodes.py

# With debug logging
python restart_nodes.py --log-level DEBUG
```

## ⚙️ Configuration

All configuration is in `config.yaml`:

### Node Configuration

```yaml
nodes:
  quorum:
    count: 5              # Number of quorum nodes
    start_port: 20000     # First HTTP port
    start_grpc_port: 10500 # First gRPC port
  non_quorum:
    count: 2
    start_port: 20005
    start_grpc_port: 10505
```

**Port Assignment:**
- Node 0: HTTP=20000, gRPC=10500
- Node 1: HTTP=20001, gRPC=10501
- ...
- Node 4: HTTP=20004, gRPC=10504
- Node 5: HTTP=20005, gRPC=10505
- Node 6: HTTP=20006, gRPC=10506

### Binary Configuration

```yaml
binaries:
  rubixgoplatform:
    repo: "https://github.com/rubixchain/rubixgoplatform.git"
    branch: "main"
  ipfs:
    version: "v0.21.0"
```

### Path Configuration

```yaml
paths:
  workspace: "./rubix-workspace"
  binaries: "{workspace}/bin"
  data: "{workspace}/data"
  logs: "{workspace}/logs"
  config: "{workspace}/config"
```

### Security Configuration

```yaml
security:
  allow_default_passwords: true  # Default: true for easy development
  password_env_vars:
    priv_pwd: "RUBIX_PRIV_PWD"
    quorum_pwd: "RUBIX_QUORUM_PWD"
```

**Default Behavior (Development):**
- Default passwords are **ENABLED** by default
- You can run `python setup.py` without any password configuration
- Uses `mypassword` for both `priv_pwd` and `quorum_pwd`

**For Production - Setting Custom Passwords:**

Option 1 - Environment Variables:
```bash
export RUBIX_PRIV_PWD="your_secure_password"
export RUBIX_QUORUM_PWD="your_quorum_password"
```

Option 2 - Use `.env` file:
```bash
cp .env.example .env
# Edit .env with your passwords
source .env
```

Option 3 - Disable default passwords and force prompts:
```yaml
security:
  allow_default_passwords: false  # Will prompt for passwords
```

### Timeout Configuration

```yaml
timeouts:
  node_startup: 40          # Seconds to wait for node startup
  http_request: 10          # HTTP request timeout
  health_check_interval: 5  # Seconds between health checks
  max_health_checks: 12     # Maximum health check attempts
  command_timeout: 60       # Default command timeout
```

### Logging Configuration

```yaml
logging:
  level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  file_enabled: true
  console_enabled: true
```

## 🔧 Configuration Examples

### Example 1: Default Setup (5 Quorum + 2 Non-Quorum)

```bash
# Uses config.yaml defaults
python setup.py
```

**Result:**
- Quorum nodes on ports 20000-20004
- Non-quorum nodes on ports 20005-20006

### Example 2: More Nodes

Edit `config.yaml`:
```yaml
nodes:
  quorum:
    count: 7
  non_quorum:
    count: 3
```

```bash
python setup.py
```

**Result:**
- 7 quorum nodes (20000-20006)
- 3 non-quorum nodes (20007-20009)

### Example 3: Custom Port Range

Edit `config.yaml`:
```yaml
nodes:
  quorum:
    count: 5
    start_port: 30000
    start_grpc_port: 15000
  non_quorum:
    count: 2
    start_port: 30005
    start_grpc_port: 15005
```

**Result:**
- Nodes use ports 30000-30006 (HTTP)
- Nodes use ports 15000-15006 (gRPC)

### Example 4: Environment Variable Overrides

```bash
# Override node counts without editing config
RUBIX_QUORUM_COUNT=10 RUBIX_NON_QUORUM_COUNT=5 python setup.py
```

### Example 5: Multiple Independent Setups

**Setup 1 - Development:**
```yaml
# config-dev.yaml
nodes:
  quorum:
    count: 3
    start_port: 20000
paths:
  workspace: "./workspace-dev"
```

**Setup 2 - Testing:**
```yaml
# config-test.yaml
nodes:
  quorum:
    count: 5
    start_port: 30000
paths:
  workspace: "./workspace-test"
```

```bash
# Run separately
python setup.py --config config-dev.yaml
python setup.py --config config-test.yaml
```

## 📁 File Structure

```
rubix-testnet-scripts/
├── config.yaml                 # Main configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
│
├── setup.py                    # Main setup script (NEW)
├── stop.py                     # Stop nodes script (NEW)
├── restart_nodes.py            # Restart script (NEW)
│
├── config_loader.py            # Configuration management
├── path_manager.py             # Path management
├── state_manager.py            # State tracking
├── logger.py                   # Logging system
├── security.py                 # Password management
├── validators.py               # Input validation
├── command_runner.py           # Secure command execution
├── health_check.py             # Health checking
├── exceptions.py               # Custom exceptions
├── install.py                  # Installation module
├── node_manager.py             # Node management
│
├── test_new_infrastructure.py  # Test suite
├── TESTING_GUIDE.md            # Testing documentation
├── README.md                   # This file
│
└── rubix-workspace/            # Created at runtime
    ├── rubixgoplatform/        # Cloned repository
    │   └── linux/mac/windows/  # Built binaries
    ├── data/                   # Node data
    ├── logs/                   # Log files
    ├── config/                 # Runtime configs
    └── .rubix-state.json       # State tracking
```

## 🐛 Troubleshooting

### Port Already in Use

**Error:** `Port 20000 is already in use`

**Solution 1:** Change ports in `config.yaml`:
```yaml
nodes:
  quorum:
    start_port: 21000
```

**Solution 2:** Find and kill conflicting process:
```bash
# macOS/Linux
lsof -i :20000
kill -9 <PID>

# Windows
netstat -ano | findstr :20000
taskkill /PID <PID> /F
```

### Node Failed to Start

**Check logs:**
```bash
tail -f rubix-workspace/logs/rubix-setup.log
tail -f rubix-workspace/logs/node0.log
```

**Common causes:**
- Port conflicts
- Missing dependencies (make, git, tmux)
- Insufficient permissions
- Low disk space

### Build Failures

**Missing Make:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows
choco install make
```

### IPFS Download Fails

**Solution:** Check internet connection or try different version:
```yaml
binaries:
  ipfs:
    version: "v0.22.0"  # Try newer version
```

### Health Check Timeouts

**Solution:** Increase timeouts in `config.yaml`:
```yaml
timeouts:
  node_startup: 60
  max_health_checks: 20
  health_check_interval: 10
```

### Permission Denied

```bash
# Make scripts executable
chmod +x setup.py stop.py restart_nodes.py

# Fix workspace permissions
chmod -R 755 rubix-workspace/
```

## 🔒 Security Best Practices

1. **Never commit passwords**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use strong passwords in production**
   ```bash
   export RUBIX_PRIV_PWD="$(openssl rand -base64 32)"
   export RUBIX_QUORUM_PWD="$(openssl rand -base64 32)"
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 config.yaml .env
   chmod 700 rubix-workspace/
   ```

4. **Use firewall rules**
   - Only expose necessary ports
   - Use localhost for development

## 🧪 Testing

### Test Infrastructure Components

```bash
# Run comprehensive test suite
python test_new_infrastructure.py
```

Expected output: `8/8 tests passed`

### Test Configuration

```bash
# Verify config loads correctly
python -c "
from config_loader import load_config
config = load_config()
print(f'Quorum nodes: {config.quorum_nodes.count}')
print(f'Total nodes: {config.get_total_node_count()}')
"
```

## 📚 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `RUBIX_PRIV_PWD` | Private key password | `mypassword` |
| `RUBIX_QUORUM_PWD` | Quorum password | `mypassword` |
| `RUBIX_QUORUM_COUNT` | Override quorum node count | `10` |
| `RUBIX_NON_QUORUM_COUNT` | Override non-quorum count | `5` |
| `RUBIX_WORKSPACE` | Custom workspace path | `/opt/rubix` |
| `RUBIX_LOG_LEVEL` | Override log level | `DEBUG` |

## 📊 Monitoring

### Check Node Status

```bash
# View logs
tail -f rubix-workspace/logs/rubix-setup.log

# Check specific node
tail -f rubix-workspace/logs/node0.log

# Check state
cat rubix-workspace/.rubix-state.json | python -m json.tool
```

### Verify Nodes Are Running

```bash
# Check if node is responding
curl http://localhost:20000/api/getalldid

# Check all quorum nodes
for port in {20000..20004}; do
  echo "Node on port $port:"
  curl -s http://localhost:$port/api/getalldid || echo "Not responding"
done
```
