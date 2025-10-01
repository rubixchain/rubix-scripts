"""Path management for Rubix testnet scripts."""

import platform
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class PlatformInfo:
    """Platform information for binary selection."""
    os_name: str  # "linux", "mac", "windows"
    build_folder: str  # Directory name in rubixgoplatform build output
    archive_suffix: str  # For IPFS binary downloads
    binary_extension: str  # ".exe" for Windows, "" for Unix


class PathManager:
    """Centralized path management for all Rubix operations."""

    def __init__(self, workspace_root: Path):
        """
        Initialize path manager.

        Args:
            workspace_root: Root directory for all Rubix operations
        """
        self.workspace = workspace_root.resolve()
        self.binaries = self.workspace / "bin"
        self.data = self.workspace / "data"
        self.logs = self.workspace / "logs"
        self.config_dir = self.workspace / "config"

        # Platform-specific paths
        self.platform = self._detect_platform()

        # Rubixgoplatform paths
        self.rubix_repo = self.workspace / "rubixgoplatform"
        self.build_dir = self.rubix_repo / self.platform.build_folder
        self.rubix_binary = self.build_dir / f"rubixgoplatform{self.platform.binary_extension}"

        # IPFS paths
        self.ipfs_binary = self.build_dir / f"ipfs{self.platform.binary_extension}"

        # Config files
        self.swarm_key = self.build_dir / "testswarm.key"
        self.quorum_list = self.build_dir / "quorumlist.json"
        self.quorum_config = self.workspace / "quorum_config.json"
        self.app_config = self.workspace / "app.node.json"
        self.state_file = self.workspace / ".rubix-state.json"

    def _detect_platform(self) -> PlatformInfo:
        """Detect the current platform and return appropriate build configuration."""
        os_name = platform.system()
        machine = platform.machine().lower()

        if os_name == "Linux":
            return PlatformInfo(
                os_name="Linux",
                build_folder="linux",
                archive_suffix="linux-amd64",
                binary_extension=""
            )
        elif os_name == "Darwin":
            # Detect ARM vs Intel Mac
            if machine in ["arm64", "aarch64"]:
                return PlatformInfo(
                    os_name="Darwin",
                    build_folder="mac",
                    archive_suffix="darwin-arm64",
                    binary_extension=""
                )
            else:
                return PlatformInfo(
                    os_name="Darwin",
                    build_folder="mac",
                    archive_suffix="darwin-amd64",
                    binary_extension=""
                )
        elif os_name == "Windows":
            return PlatformInfo(
                os_name="Windows",
                build_folder="windows",
                archive_suffix="windows-amd64",
                binary_extension=".exe"
            )
        else:
            raise RuntimeError(f"Unsupported operating system: {os_name}")

    def get_node_data_dir(self, node_idx: int) -> Path:
        """Get data directory for a specific node."""
        return self.data / f"node{node_idx}"

    def get_node_log_file(self, node_idx: int) -> Path:
        """Get log file path for a specific node."""
        return self.logs / f"node{node_idx}.log"

    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            self.workspace,
            self.binaries,
            self.data,
            self.logs,
            self.config_dir,
            self.build_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_ipfs_download_url(self, version: str) -> str:
        """Get the download URL for IPFS binary based on platform."""
        base_url = "https://github.com/ipfs/kubo/releases/download"

        if self.platform.os_name == "Windows":
            return f"{base_url}/{version}/kubo_{version}_{self.platform.archive_suffix}.zip"
        else:
            return f"{base_url}/{version}/kubo_{version}_{self.platform.archive_suffix}.tar.gz"

    def get_ipfs_archive_name(self, version: str) -> str:
        """Get the archive filename for IPFS download."""
        if self.platform.os_name == "Windows":
            return f"kubo_{version}_{self.platform.archive_suffix}.zip"
        else:
            return f"kubo_{version}_{self.platform.archive_suffix}.tar.gz"

    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.platform.os_name == "Windows"

    def is_mac(self) -> bool:
        """Check if running on macOS."""
        return self.platform.os_name == "Darwin"

    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.platform.os_name == "Linux"

    def __str__(self) -> str:
        """String representation of path manager."""
        return (
            f"PathManager(\n"
            f"  workspace={self.workspace}\n"
            f"  platform={self.platform.os_name} ({self.platform.archive_suffix})\n"
            f"  rubix_binary={self.rubix_binary}\n"
            f"  ipfs_binary={self.ipfs_binary}\n"
            f")"
        )
