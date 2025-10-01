"""State management for tracking installation and node status."""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    """Possible node states."""
    UNKNOWN = "unknown"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class InstallationState:
    """Tracks installation progress and node states."""

    def __init__(self, state_file: Path):
        """
        Initialize state manager.

        Args:
            state_file: Path to the state JSON file
        """
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from file or create default state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                return self._create_default_state()
        else:
            return self._create_default_state()

    def _create_default_state(self) -> Dict[str, Any]:
        """Create default state structure."""
        return {
            "version": "1.0",
            "last_updated": None,
            "installation": {
                "rubixgoplatform_cloned": False,
                "rubixgoplatform_built": False,
                "ipfs_downloaded": False,
                "swarm_key_downloaded": False
            },
            "nodes": {}
        }

    def save(self) -> None:
        """Save current state to file."""
        self.state["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first, then rename (atomic operation)
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(self.state, f, indent=2)

        temp_file.replace(self.state_file)

    # Installation state methods
    def is_rubixgoplatform_cloned(self) -> bool:
        """Check if rubixgoplatform repository is cloned."""
        return self.state["installation"].get("rubixgoplatform_cloned", False)

    def set_rubixgoplatform_cloned(self, value: bool = True) -> None:
        """Mark rubixgoplatform as cloned."""
        self.state["installation"]["rubixgoplatform_cloned"] = value
        self.save()

    def is_rubixgoplatform_built(self) -> bool:
        """Check if rubixgoplatform is built."""
        return self.state["installation"].get("rubixgoplatform_built", False)

    def set_rubixgoplatform_built(self, value: bool = True) -> None:
        """Mark rubixgoplatform as built."""
        self.state["installation"]["rubixgoplatform_built"] = value
        self.save()

    def is_ipfs_downloaded(self) -> bool:
        """Check if IPFS binary is downloaded."""
        return self.state["installation"].get("ipfs_downloaded", False)

    def set_ipfs_downloaded(self, value: bool = True) -> None:
        """Mark IPFS as downloaded."""
        self.state["installation"]["ipfs_downloaded"] = value
        self.save()

    def is_swarm_key_downloaded(self) -> bool:
        """Check if swarm key is downloaded."""
        return self.state["installation"].get("swarm_key_downloaded", False)

    def set_swarm_key_downloaded(self, value: bool = True) -> None:
        """Mark swarm key as downloaded."""
        self.state["installation"]["swarm_key_downloaded"] = value
        self.save()

    def is_installation_complete(self) -> bool:
        """Check if all installation steps are complete."""
        installation = self.state["installation"]
        return all([
            installation.get("rubixgoplatform_cloned", False),
            installation.get("rubixgoplatform_built", False),
            installation.get("ipfs_downloaded", False),
            installation.get("swarm_key_downloaded", False)
        ])

    # Node state methods
    def get_node_state(self, node_idx: int) -> Dict[str, Any]:
        """
        Get state for a specific node.

        Args:
            node_idx: Node index

        Returns:
            Dictionary with node state
        """
        node_key = f"node{node_idx}"
        if node_key not in self.state["nodes"]:
            self.state["nodes"][node_key] = {
                "status": NodeStatus.UNKNOWN.value,
                "pid": None,
                "did": None,
                "peer_id": None,
                "port": None,
                "grpc_port": None,
                "last_started": None,
                "last_stopped": None
            }
        return self.state["nodes"][node_key]

    def set_node_status(self, node_idx: int, status: NodeStatus) -> None:
        """Set status for a specific node."""
        node_state = self.get_node_state(node_idx)
        node_state["status"] = status.value

        if status == NodeStatus.RUNNING:
            node_state["last_started"] = datetime.utcnow().isoformat() + "Z"
        elif status in [NodeStatus.STOPPED, NodeStatus.FAILED]:
            node_state["last_stopped"] = datetime.utcnow().isoformat() + "Z"

        self.save()

    def set_node_info(self, node_idx: int, pid: Optional[int] = None,
                      did: Optional[str] = None, peer_id: Optional[str] = None,
                      port: Optional[int] = None, grpc_port: Optional[int] = None) -> None:
        """Update node information."""
        node_state = self.get_node_state(node_idx)

        if pid is not None:
            node_state["pid"] = pid
        if did is not None:
            node_state["did"] = did
        if peer_id is not None:
            node_state["peer_id"] = peer_id
        if port is not None:
            node_state["port"] = port
        if grpc_port is not None:
            node_state["grpc_port"] = grpc_port

        self.save()

    def get_node_did(self, node_idx: int) -> Optional[str]:
        """Get DID for a specific node."""
        return self.get_node_state(node_idx).get("did")

    def get_node_peer_id(self, node_idx: int) -> Optional[str]:
        """Get peer ID for a specific node."""
        return self.get_node_state(node_idx).get("peer_id")

    def get_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get all node states."""
        return self.state["nodes"]

    def get_running_nodes(self) -> list[int]:
        """Get list of node indices that are marked as running."""
        running = []
        for node_key, node_state in self.state["nodes"].items():
            if node_state.get("status") == NodeStatus.RUNNING.value:
                node_idx = int(node_key.replace("node", ""))
                running.append(node_idx)
        return sorted(running)

    def clear_installation_state(self) -> None:
        """Clear installation state (for --clean operations)."""
        self.state["installation"] = {
            "rubixgoplatform_cloned": False,
            "rubixgoplatform_built": False,
            "ipfs_downloaded": False,
            "swarm_key_downloaded": False
        }
        self.save()

    def clear_node_state(self, node_idx: Optional[int] = None) -> None:
        """
        Clear node state.

        Args:
            node_idx: If specified, clear only this node. Otherwise clear all nodes.
        """
        if node_idx is not None:
            node_key = f"node{node_idx}"
            if node_key in self.state["nodes"]:
                del self.state["nodes"][node_key]
        else:
            self.state["nodes"] = {}

        self.save()

    def clear_all(self) -> None:
        """Clear all state."""
        self.state = self._create_default_state()
        self.save()

    def get_state_summary(self) -> str:
        """Get a human-readable summary of current state."""
        lines = []
        lines.append("=== Installation State ===")
        inst = self.state["installation"]
        lines.append(f"  Rubix cloned: {inst.get('rubixgoplatform_cloned', False)}")
        lines.append(f"  Rubix built: {inst.get('rubixgoplatform_built', False)}")
        lines.append(f"  IPFS downloaded: {inst.get('ipfs_downloaded', False)}")
        lines.append(f"  Swarm key: {inst.get('swarm_key_downloaded', False)}")

        lines.append("\n=== Node State ===")
        if not self.state["nodes"]:
            lines.append("  No nodes initialized")
        else:
            for node_key in sorted(self.state["nodes"].keys()):
                node_state = self.state["nodes"][node_key]
                status = node_state.get("status", "unknown")
                port = node_state.get("port", "N/A")
                did = node_state.get("did", "N/A")
                if did and len(did) > 20:
                    did = did[:20] + "..."
                lines.append(f"  {node_key}: {status} (port={port}, did={did})")

        return "\n".join(lines)
