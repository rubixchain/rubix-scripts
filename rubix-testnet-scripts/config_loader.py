"""Configuration loader for Rubix testnet scripts."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class NodeGroupConfig:
    """Configuration for a group of nodes (quorum or non-quorum)."""
    count: int
    start_port: int
    start_grpc_port: int


@dataclass
class BinaryConfig:
    """Configuration for binary sources."""
    rubixgoplatform_repo: str
    rubixgoplatform_branch: str
    ipfs_version: str


@dataclass
class PathConfig:
    """Paths configuration."""
    workspace: Path
    binaries: Path
    data: Path
    logs: Path
    config: Path


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    node_startup: int
    http_request: int
    health_check_interval: int
    max_health_checks: int
    command_timeout: int


@dataclass
class SecurityConfig:
    """Security configuration."""
    allow_default_passwords: bool
    password_env_vars: Dict[str, str]
    default_passwords: Dict[str, str]


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    format: str
    file_enabled: bool
    console_enabled: bool


class Config:
    """Main configuration class with all settings."""

    def __init__(self, config_dict: Dict[str, Any], config_path: Path):
        self.config_path = config_path
        self._raw = config_dict

        # Parse node configurations
        nodes = config_dict.get('nodes', {})
        self.quorum_nodes = NodeGroupConfig(
            count=nodes.get('quorum', {}).get('count', 5),
            start_port=nodes.get('quorum', {}).get('start_port', 20000),
            start_grpc_port=nodes.get('quorum', {}).get('start_grpc_port', 10500)
        )
        self.non_quorum_nodes = NodeGroupConfig(
            count=nodes.get('non_quorum', {}).get('count', 2),
            start_port=nodes.get('non_quorum', {}).get('start_port', 20005),
            start_grpc_port=nodes.get('non_quorum', {}).get('start_grpc_port', 10505)
        )

        # Parse binary configurations
        binaries = config_dict.get('binaries', {})
        self.binaries = BinaryConfig(
            rubixgoplatform_repo=binaries.get('rubixgoplatform', {}).get('repo',
                'https://github.com/rubixchain/rubixgoplatform.git'),
            rubixgoplatform_branch=binaries.get('rubixgoplatform', {}).get('branch', 'main'),
            ipfs_version=binaries.get('ipfs', {}).get('version', 'v0.21.0')
        )

        # Parse paths with variable substitution
        paths = config_dict.get('paths', {})
        workspace = Path(paths.get('workspace', './rubix-workspace')).resolve()

        self.paths = PathConfig(
            workspace=workspace,
            binaries=self._resolve_path(paths.get('binaries', '{workspace}/bin'), workspace),
            data=self._resolve_path(paths.get('data', '{workspace}/data'), workspace),
            logs=self._resolve_path(paths.get('logs', '{workspace}/logs'), workspace),
            config=self._resolve_path(paths.get('config', '{workspace}/config'), workspace)
        )

        # Parse timeouts
        timeouts = config_dict.get('timeouts', {})
        self.timeouts = TimeoutConfig(
            node_startup=timeouts.get('node_startup', 40),
            http_request=timeouts.get('http_request', 10),
            health_check_interval=timeouts.get('health_check_interval', 5),
            max_health_checks=timeouts.get('max_health_checks', 12),
            command_timeout=timeouts.get('command_timeout', 60)
        )

        # Parse security settings
        security = config_dict.get('security', {})
        self.security = SecurityConfig(
            allow_default_passwords=security.get('allow_default_passwords', False),
            password_env_vars=security.get('password_env_vars', {
                'priv_pwd': 'RUBIX_PRIV_PWD',
                'quorum_pwd': 'RUBIX_QUORUM_PWD'
            }),
            default_passwords=security.get('default_passwords', {
                'priv_pwd': 'mypassword',
                'quorum_pwd': 'mypassword'
            })
        )

        # Parse logging settings
        logging = config_dict.get('logging', {})
        self.logging = LoggingConfig(
            level=logging.get('level', 'INFO'),
            format=logging.get('format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s'),
            file_enabled=logging.get('file_enabled', True),
            console_enabled=logging.get('console_enabled', True)
        )

    def _resolve_path(self, path_str: str, workspace: Path) -> Path:
        """Resolve path with variable substitution."""
        resolved = path_str.replace('{workspace}', str(workspace))
        return Path(resolved).resolve()

    def get_total_node_count(self) -> int:
        """Get total number of nodes."""
        return self.quorum_nodes.count + self.non_quorum_nodes.count

    def get_node_port(self, node_idx: int) -> int:
        """Get the server port for a given node index."""
        if node_idx < self.quorum_nodes.count:
            return self.quorum_nodes.start_port + node_idx
        else:
            offset = node_idx - self.quorum_nodes.count
            return self.non_quorum_nodes.start_port + offset

    def get_node_grpc_port(self, node_idx: int) -> int:
        """Get the gRPC port for a given node index."""
        if node_idx < self.quorum_nodes.count:
            return self.quorum_nodes.start_grpc_port + node_idx
        else:
            offset = node_idx - self.quorum_nodes.count
            return self.non_quorum_nodes.start_grpc_port + offset

    def is_quorum_node(self, node_idx: int) -> bool:
        """Check if a node index is a quorum node."""
        return node_idx < self.quorum_nodes.count


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yaml in script directory.

    Returns:
        Config object with all settings.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    if config_path is None:
        # Look for config.yaml in the script directory
        script_dir = Path(__file__).parent
        config_path = script_dir / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    # Apply environment variable overrides
    config_dict = _apply_env_overrides(config_dict)

    return Config(config_dict, config_path)


def _apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    # Example: RUBIX_QUORUM_COUNT=7 overrides nodes.quorum.count

    # Quorum node count
    if env_val := os.getenv('RUBIX_QUORUM_COUNT'):
        config_dict.setdefault('nodes', {}).setdefault('quorum', {})['count'] = int(env_val)

    # Non-quorum node count
    if env_val := os.getenv('RUBIX_NON_QUORUM_COUNT'):
        config_dict.setdefault('nodes', {}).setdefault('non_quorum', {})['count'] = int(env_val)

    # Workspace path
    if env_val := os.getenv('RUBIX_WORKSPACE'):
        config_dict.setdefault('paths', {})['workspace'] = env_val

    # Log level
    if env_val := os.getenv('RUBIX_LOG_LEVEL'):
        config_dict.setdefault('logging', {})['level'] = env_val

    return config_dict


# Global config instance (loaded on first import)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config
