"""
Refactored installation module for Rubix prerequisites.
Handles cloning, building, and downloading dependencies with idempotency.
"""

import os
import shutil
import requests
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

from logger import get_logger, log_section, log_step
from path_manager import PathManager
from state_manager import InstallationState
from config_loader import Config
from command_runner import run_command
from exceptions import DependencyError, DownloadError, CommandError


class RubixInstaller:
    """Handles installation of Rubix prerequisites."""

    def __init__(self, paths: PathManager, config: Config, state: InstallationState):
        """
        Initialize installer.

        Args:
            paths: Path manager instance
            config: Configuration instance
            state: State manager instance
        """
        self.paths = paths
        self.config = config
        self.state = state
        self.logger = get_logger()

    def install_all(self, force: bool = False) -> None:
        """
        Install all prerequisites.

        Args:
            force: If True, reinstall even if already installed
        """
        log_section("Installing Rubix Prerequisites")

        total_steps = 4
        current_step = 0

        # Step 1: Clone rubixgoplatform
        current_step += 1
        if force or not self.state.is_rubixgoplatform_cloned():
            log_step(current_step, total_steps, "Cloning rubixgoplatform repository")
            self.clone_rubixgoplatform()
        else:
            log_step(current_step, total_steps, "Rubixgoplatform already cloned (skipping)")

        # Step 2: Build rubixgoplatform
        current_step += 1
        if force or not self.state.is_rubixgoplatform_built():
            log_step(current_step, total_steps, "Building rubixgoplatform")
            self.build_rubixgoplatform()
        else:
            log_step(current_step, total_steps, "Rubixgoplatform already built (skipping)")

        # Step 3: Download IPFS
        current_step += 1
        if force or not self.state.is_ipfs_downloaded():
            log_step(current_step, total_steps, "Downloading IPFS binary")
            self.download_ipfs()
        else:
            log_step(current_step, total_steps, "IPFS already downloaded (skipping)")

        # Step 4: Download swarm key
        current_step += 1
        if force or not self.state.is_swarm_key_downloaded():
            log_step(current_step, total_steps, "Downloading test swarm key")
            self.download_swarm_key()
        else:
            log_step(current_step, total_steps, "Swarm key already downloaded (skipping)")

        self.logger.info("✓ All prerequisites installed successfully")

    def clone_rubixgoplatform(self) -> None:
        """Clone the rubixgoplatform repository."""
        repo_url = self.config.binaries.rubixgoplatform_repo
        branch = self.config.binaries.rubixgoplatform_branch

        # Check if already exists
        if self.paths.rubix_repo.exists():
            self.logger.info(f"Repository already exists at {self.paths.rubix_repo}")

            # Verify it's the correct repo
            try:
                result = run_command(
                    ["git", "-C", str(self.paths.rubix_repo), "remote", "get-url", "origin"],
                    timeout=10,
                    check=False
                )

                if result.success and repo_url in result.stdout:
                    self.logger.info("✓ Existing repository verified")
                    self.state.set_rubixgoplatform_cloned(True)
                    return
                else:
                    self.logger.warning("Existing directory is not the correct repository, removing...")
                    shutil.rmtree(self.paths.rubix_repo)
            except Exception as e:
                self.logger.warning(f"Could not verify existing repo: {e}, removing...")
                shutil.rmtree(self.paths.rubix_repo)

        # Clone the repository
        self.logger.info(f"Cloning {repo_url} (branch: {branch})...")

        try:
            # Clone to workspace
            run_command(
                ["git", "clone", "-b", branch, repo_url, str(self.paths.rubix_repo)],
                timeout=300,  # 5 minutes for cloning
                cwd=str(self.paths.workspace)
            )

            self.logger.info(f"✓ Repository cloned to {self.paths.rubix_repo}")
            self.state.set_rubixgoplatform_cloned(True)

        except CommandError as e:
            raise DependencyError(
                "rubixgoplatform",
                f"Failed to clone repository: {e}"
            )

    def build_rubixgoplatform(self) -> None:
        """Build rubixgoplatform for the current platform."""
        if not self.paths.rubix_repo.exists():
            raise DependencyError(
                "rubixgoplatform",
                "Repository not cloned. Run clone_rubixgoplatform() first."
            )

        # Determine build command based on platform
        if self.paths.platform.os_name == "Windows":
            build_target = "compile-windows"
        elif self.paths.platform.os_name == "Linux":
            build_target = "compile-linux"
        elif self.paths.platform.os_name == "Darwin":
            build_target = "compile-mac"
        else:
            raise DependencyError(
                "rubixgoplatform",
                f"Unsupported platform: {self.paths.platform.os_name}"
            )

        self.logger.info(f"Building rubixgoplatform (target: {build_target})...")

        try:
            # Ensure build directory exists
            self.paths.build_dir.mkdir(parents=True, exist_ok=True)

            # Run make command
            run_command(
                ["make", build_target],
                timeout=600,  # 10 minutes for building
                cwd=str(self.paths.rubix_repo)
            )

            # Verify binary was created
            if not self.paths.rubix_binary.exists():
                raise DependencyError(
                    "rubixgoplatform",
                    f"Build completed but binary not found at {self.paths.rubix_binary}"
                )

            self.logger.info(f"✓ Binary built at {self.paths.rubix_binary}")
            self.state.set_rubixgoplatform_built(True)

        except CommandError as e:
            raise DependencyError(
                "rubixgoplatform",
                f"Failed to build: {e}"
            )

    def download_ipfs(self) -> None:
        """Download and install IPFS binary."""
        version = self.config.binaries.ipfs_version
        download_url = self.paths.get_ipfs_download_url(version)
        archive_name = self.paths.get_ipfs_archive_name(version)

        # Download to workspace
        archive_path = self.paths.workspace / archive_name

        self.logger.info(f"Downloading IPFS {version} from {download_url}...")

        try:
            # Download
            response = requests.get(download_url, timeout=300, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            self.logger.info(f"Downloading {total_size / 1024 / 1024:.2f} MB...")

            with open(archive_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info("✓ Download complete")

        except requests.RequestException as e:
            raise DownloadError(download_url, str(e))

        # Extract archive
        self.logger.info("Extracting IPFS binary...")
        extract_dir = self.paths.workspace / "kubo-temp"

        try:
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)

            # Find and move IPFS binary
            ipfs_bin_name = "ipfs" + self.paths.platform.binary_extension
            src_binary = extract_dir / "kubo" / ipfs_bin_name

            if not src_binary.exists():
                raise DependencyError(
                    "ipfs",
                    f"IPFS binary not found in archive at {src_binary}"
                )

            # Ensure build directory exists
            self.paths.build_dir.mkdir(parents=True, exist_ok=True)

            # Move to build directory
            shutil.move(str(src_binary), str(self.paths.ipfs_binary))

            # Make executable on Unix
            if not self.paths.is_windows():
                self.paths.ipfs_binary.chmod(0o755)

            self.logger.info(f"✓ IPFS binary installed at {self.paths.ipfs_binary}")

            # Cleanup
            archive_path.unlink()
            shutil.rmtree(extract_dir)

            self.state.set_ipfs_downloaded(True)

        except Exception as e:
            # Cleanup on failure
            if archive_path.exists():
                archive_path.unlink()
            if extract_dir.exists():
                shutil.rmtree(extract_dir)

            raise DependencyError("ipfs", f"Failed to extract: {e}")

    def download_swarm_key(self) -> None:
        """Download the test swarm key."""
        swarm_key_url = "https://raw.githubusercontent.com/rubixchain/rubixgoplatform/main/testswarm.key"

        self.logger.info(f"Downloading test swarm key from {swarm_key_url}...")

        try:
            # Ensure build directory exists
            self.paths.build_dir.mkdir(parents=True, exist_ok=True)

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(swarm_key_url, headers=headers, timeout=30)
            response.raise_for_status()

            with open(self.paths.swarm_key, 'wb') as f:
                f.write(response.content)

            self.logger.info(f"✓ Swarm key saved to {self.paths.swarm_key}")
            self.state.set_swarm_key_downloaded(True)

        except requests.RequestException as e:
            raise DownloadError(swarm_key_url, str(e))

    def verify_installation(self) -> bool:
        """
        Verify all components are installed correctly.

        Returns:
            True if all components are present and valid
        """
        self.logger.info("Verifying installation...")

        checks = [
            (self.paths.rubix_binary.exists(), f"Rubix binary at {self.paths.rubix_binary}"),
            (self.paths.ipfs_binary.exists(), f"IPFS binary at {self.paths.ipfs_binary}"),
            (self.paths.swarm_key.exists(), f"Swarm key at {self.paths.swarm_key}"),
        ]

        all_ok = True
        for check, description in checks:
            if check:
                self.logger.info(f"✓ {description}")
            else:
                self.logger.error(f"✗ Missing: {description}")
                all_ok = False

        return all_ok
