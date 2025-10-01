"""
Node management module for Rubix nodes.
Handles starting, stopping, and managing Rubix blockchain nodes.
"""

import re
import time
import json
from pathlib import Path
from typing import Optional, Dict, List

from logger import get_logger, log_node_info
from path_manager import PathManager
from state_manager import InstallationState, NodeStatus
from config_loader import Config
from command_runner import run_command
from health_check import wait_for_node_ready
from security import PasswordManager
from exceptions import (
    NodeStartupError, NodeCommunicationError, DIDCreationError,
    DIDRegistrationError, CommandError
)


class RubixNodeManager:
    """Manages Rubix blockchain nodes."""

    def __init__(
        self,
        paths: PathManager,
        config: Config,
        state: InstallationState,
        password_mgr: PasswordManager
    ):
        """
        Initialize node manager.

        Args:
            paths: Path manager instance
            config: Configuration instance
            state: State manager instance
            password_mgr: Password manager instance
        """
        self.paths = paths
        self.config = config
        self.state = state
        self.password_mgr = password_mgr
        self.logger = get_logger()

    def start_node(self, node_idx: int) -> tuple[int, int]:
        """
        Start a Rubix node.

        Args:
            node_idx: Node index

        Returns:
            Tuple of (server_port, grpc_port)

        Raises:
            NodeStartupError: If node fails to start
        """
        node_name = f"node{node_idx}"
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Starting on ports HTTP={server_port}, gRPC={grpc_port}")

        # Build command based on platform
        rubix_binary = str(self.paths.rubix_binary)

        if self.paths.is_windows():
            # Windows: Use PowerShell to start in background
            cmd = [
                "powershell", "-Command",
                f"Start-Process -FilePath '{rubix_binary}' "
                f"-ArgumentList 'run -p {node_name} -n {node_idx} -s -testNet -grpcPort {grpc_port}' "
                f"-WindowStyle Hidden"
            ]
        else:
            # Linux/Mac: Use tmux
            cmd = [
                "tmux", "new", "-s", node_name, "-d",
                rubix_binary, "run",
                "-p", node_name,
                "-n", str(node_idx),
                "-s",
                "-testNet",
                "-grpcPort", str(grpc_port)
            ]

        try:
            run_command(cmd, timeout=30, cwd=str(self.paths.build_dir))

            # Wait for node to become ready
            log_node_info(node_idx, "Waiting for node to become ready...")
            wait_for_node_ready(server_port, node_idx, self.config)

            # Update state
            self.state.set_node_status(node_idx, NodeStatus.RUNNING)
            self.state.set_node_info(node_idx, port=server_port, grpc_port=grpc_port)

            log_node_info(node_idx, "✓ Node started successfully")

            return server_port, grpc_port

        except Exception as e:
            self.state.set_node_status(node_idx, NodeStatus.FAILED)
            raise NodeStartupError(node_idx, str(e))

    def stop_node(self, node_idx: int) -> None:
        """
        Stop a Rubix node gracefully.

        Args:
            node_idx: Node index
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Stopping node on port {server_port}")

        try:
            cmd = [
                str(self.paths.rubix_binary),
                "shutdown",
                "-port", str(server_port),
                "-grpcPort", str(grpc_port)
            ]

            run_command(cmd, timeout=30, cwd=str(self.paths.build_dir), check=False)

            self.state.set_node_status(node_idx, NodeStatus.STOPPED)
            log_node_info(node_idx, "✓ Node stopped")

        except Exception as e:
            self.logger.warning(f"[Node {node_idx}] Failed to stop gracefully: {e}")

    def create_did(
        self,
        node_idx: int,
        did_type: int = 4,
        did_alias: Optional[str] = None
    ) -> str:
        """
        Create a DID on a node.

        Args:
            node_idx: Node index
            did_type: DID type (default: 4)
            did_alias: Alias for the DID (for tracking)

        Returns:
            Created DID string

        Raises:
            DIDCreationError: If DID creation fails
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Creating DID (type={did_type})")

        priv_pwd = self.password_mgr.get_priv_password()
        quorum_pwd = self.password_mgr.get_quorum_password()

        cmd = [
            str(self.paths.rubix_binary),
            "createdid",
            "-port", str(server_port),
            "-grpcPort", str(grpc_port),
            "-didType", str(did_type),
            "-privPWD", priv_pwd,
            "-quorumPWD", quorum_pwd
        ]

        try:
            result = run_command(cmd, timeout=60, cwd=str(self.paths.build_dir))

            # Extract DID from output
            if "successfully" in result.stderr.lower():
                pattern = r'bafybmi\w+'
                matches = re.findall(pattern, result.stderr)
                if matches:
                    did = matches[0]
                    log_node_info(node_idx, f"✓ DID created: {did}")

                    # Store in state
                    if did_alias:
                        # Store DID with alias in node state
                        node_state = self.state.get_node_state(node_idx)
                        if "dids" not in node_state:
                            node_state["dids"] = {}
                        node_state["dids"][did_alias] = {"did": did, "did_type": did_type}
                        self.state.save()

                    return did
                else:
                    raise DIDCreationError(node_idx, "Could not extract DID from output")
            else:
                raise DIDCreationError(node_idx, f"Unexpected output: {result.stderr}")

        except CommandError as e:
            raise DIDCreationError(node_idx, str(e))

    def register_did(self, node_idx: int, did: str) -> None:
        """
        Register a DID.

        Args:
            node_idx: Node index
            did: DID to register

        Raises:
            DIDRegistrationError: If registration fails
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Registering DID: {did}")

        priv_pwd = self.password_mgr.get_priv_password()

        cmd = [
            str(self.paths.rubix_binary),
            "registerdid",
            "-did", did,
            "-port", str(server_port),
            "-grpcPort", str(grpc_port),
            "-privPWD", priv_pwd
        ]

        try:
            run_command(cmd, timeout=60, cwd=str(self.paths.build_dir))
            log_node_info(node_idx, f"✓ DID registered: {did}")

        except CommandError as e:
            raise DIDRegistrationError(did, str(e))

    def fund_did(self, node_idx: int, did: str, amount: int = 70) -> None:
        """
        Fund a DID with RBT tokens.

        Args:
            node_idx: Node index
            did: DID to fund
            amount: Amount of RBT tokens (default: 70)
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Funding DID {did} with {amount} RBT")

        priv_pwd = self.password_mgr.get_priv_password()

        cmd = [
            str(self.paths.rubix_binary),
            "generatetestrbt",
            "-did", did,
            "-numTokens", str(amount),
            "-port", str(server_port),
            "-grpcPort", str(grpc_port),
            "-privPWD", priv_pwd
        ]

        try:
            run_command(cmd, timeout=120, cwd=str(self.paths.build_dir))
            log_node_info(node_idx, f"✓ DID funded with {amount} RBT")

        except CommandError as e:
            self.logger.error(f"[Node {node_idx}] Failed to fund DID: {e}")
            raise

    def get_peer_id(self, node_idx: int) -> str:
        """
        Get the peer ID of a node.

        Args:
            node_idx: Node index

        Returns:
            Peer ID string

        Raises:
            NodeCommunicationError: If peer ID cannot be retrieved
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        cmd = [
            str(self.paths.rubix_binary),
            "get-peer-id",
            "-port", str(server_port),
            "-grpcPort", str(grpc_port)
        ]

        try:
            result = run_command(cmd, timeout=30, cwd=str(self.paths.build_dir))
            peer_id = result.stdout.strip()

            # Update state
            self.state.set_node_info(node_idx, peer_id=peer_id)

            log_node_info(node_idx, f"Peer ID: {peer_id}")
            return peer_id

        except CommandError as e:
            raise NodeCommunicationError(node_idx, "get-peer-id", str(e))

    def setup_quorum(self, node_idx: int, did: str) -> None:
        """
        Setup a node as a quorum.

        Args:
            node_idx: Node index
            did: Quorum DID
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Setting up quorum with DID: {did}")

        cmd = [
            str(self.paths.rubix_binary),
            "setupquorum",
            "-did", did,
            "-port", str(server_port),
            "-grpcPort", str(grpc_port)
        ]

        try:
            run_command(cmd, timeout=60, cwd=str(self.paths.build_dir))
            log_node_info(node_idx, "✓ Quorum setup complete")

        except CommandError as e:
            self.logger.error(f"[Node {node_idx}] Failed to setup quorum: {e}")
            raise

    def add_quorum_list(self, node_idx: int, quorum_list_file: Path) -> None:
        """
        Add quorum list to a node.

        Args:
            node_idx: Node index
            quorum_list_file: Path to quorumlist.json
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Adding quorum list from {quorum_list_file}")

        cmd = [
            str(self.paths.rubix_binary),
            "addquorum",
            "-port", str(server_port),
            "-grpcPort", str(grpc_port),
            "-quorumList", str(quorum_list_file)
        ]

        try:
            run_command(cmd, timeout=60, cwd=str(self.paths.build_dir))
            log_node_info(node_idx, "✓ Quorum list added")

        except CommandError as e:
            self.logger.error(f"[Node {node_idx}] Failed to add quorum list: {e}")
            raise

    def add_peer_details(
        self,
        node_idx: int,
        peer_id: str,
        did: str,
        did_type: int
    ) -> None:
        """
        Add peer details to a node.

        Args:
            node_idx: Node index
            peer_id: Peer ID to add
            did: DID of the peer
            did_type: Type of DID
        """
        server_port = self.config.get_node_port(node_idx)
        grpc_port = self.config.get_node_grpc_port(node_idx)

        log_node_info(node_idx, f"Adding peer details: {peer_id}")

        cmd = [
            str(self.paths.rubix_binary),
            "addpeerdetails",
            "-peerID", peer_id,
            "-did", did,
            "-didType", str(did_type),
            "-port", str(server_port),
            "-grpcPort", str(grpc_port)
        ]

        try:
            run_command(cmd, timeout=60, cwd=str(self.paths.build_dir))
            log_node_info(node_idx, "✓ Peer details added")

        except CommandError as e:
            self.logger.error(f"[Node {node_idx}] Failed to add peer details: {e}")
            raise
