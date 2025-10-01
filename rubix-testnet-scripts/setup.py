#!/usr/bin/env python3
"""
Rubix Testnet Setup Script (Refactored)

This is the new main entry point for setting up Rubix testnet nodes.
It replaces run.py with improved configuration, error handling, and state management.
"""

import sys
import json
import argparse
from pathlib import Path

from config_loader import load_config
from path_manager import PathManager
from state_manager import InstallationState
from logger import setup_logger, get_logger, log_section
from security import PasswordManager
from install import RubixInstaller
from node_manager import RubixNodeManager
from exceptions import RubixError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Setup Rubix testnet nodes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config.yaml
  python setup.py

  # Use custom configuration
  python setup.py --config custom-config.yaml

  # Force reinstall everything
  python setup.py --force

  # Clean start (remove all state and data)
  python setup.py --clean

  # Skip installation, only start nodes
  python setup.py --skip-install

  # Enable debug logging
  python setup.py --log-level DEBUG
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reinstall even if components already exist'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean start - remove all existing data and state'
    )

    parser.add_argument(
        '--skip-install',
        action='store_true',
        help='Skip installation phase, only setup nodes'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Override log level from config'
    )

    return parser.parse_args()


def setup_quorum_nodes(node_mgr: RubixNodeManager, config, paths: PathManager):
    """
    Setup quorum nodes.

    Args:
        node_mgr: Node manager instance
        config: Configuration instance
        paths: Path manager instance
    """
    logger = get_logger()
    log_section("Setting up Quorum Nodes")

    quorum_count = config.quorum_nodes.count
    logger.info(f"Starting {quorum_count} quorum nodes...")

    quorum_dids = []

    # Start all quorum nodes and create DIDs
    for i in range(quorum_count):
        logger.info(f"\n--- Quorum Node {i} ---")

        # Start node
        node_mgr.start_node(i)

        # Get peer ID
        peer_id = node_mgr.get_peer_id(i)

        # Create DID (type 4 for quorum, not registered)
        did = node_mgr.create_did(i, did_type=4, did_alias="did_quorum")

        # Fund DID
        node_mgr.fund_did(i, did, amount=70)

        quorum_dids.append({
            "node_idx": i,
            "did": did,
            "peer_id": peer_id,
            "type": 2,
            "address": did
        })

    # Create quorumlist.json
    logger.info("\nCreating quorumlist.json...")
    quorum_list = [{"type": 2, "address": q["did"]} for q in quorum_dids]

    with open(paths.quorum_list, 'w') as f:
        json.dump(quorum_list, f, indent=2)

    logger.info(f"✓ Quorum list saved to {paths.quorum_list}")

    # Add quorum list to all quorum nodes
    logger.info("\nAdding quorum list to all nodes...")
    for i in range(quorum_count):
        node_mgr.add_quorum_list(i, paths.quorum_list)

    # Setup quorums
    logger.info("\nSetting up quorums...")
    for i in range(quorum_count):
        did = quorum_dids[i]["did"]
        node_mgr.setup_quorum(i, did)

    logger.info(f"\n✓ All {quorum_count} quorum nodes are ready")

    return quorum_dids


def setup_non_quorum_nodes(node_mgr: RubixNodeManager, config, paths: PathManager, quorum_dids):
    """
    Setup non-quorum nodes.

    Args:
        node_mgr: Node manager instance
        config: Configuration instance
        paths: Path manager instance
        quorum_dids: List of quorum DIDs with peer info
    """
    logger = get_logger()
    log_section("Setting up Non-Quorum Nodes")

    non_quorum_count = config.non_quorum_nodes.count
    quorum_count = config.quorum_nodes.count

    logger.info(f"Starting {non_quorum_count} non-quorum nodes...")

    for i in range(non_quorum_count):
        node_idx = quorum_count + i
        logger.info(f"\n--- Non-Quorum Node {node_idx} ---")

        # Start node
        node_mgr.start_node(node_idx)

        # Create and register deployer DID
        deployer_did = node_mgr.create_did(node_idx, did_type=4, did_alias="did_deployer")
        node_mgr.register_did(node_idx, deployer_did)
        node_mgr.fund_did(node_idx, deployer_did, amount=70)

        # Create and register user DID
        user_did = node_mgr.create_did(node_idx, did_type=4, did_alias="did_user")
        node_mgr.register_did(node_idx, user_did)
        node_mgr.fund_did(node_idx, user_did, amount=70)

        # Add quorum list
        node_mgr.add_quorum_list(node_idx, paths.quorum_list)

        # Add all quorum peers
        logger.info(f"Adding {len(quorum_dids)} quorum peer details...")
        for quorum in quorum_dids:
            node_mgr.add_peer_details(
                node_idx,
                quorum["peer_id"],
                quorum["did"],
                quorum["type"]
            )

        logger.info(f"✓ Non-quorum node {node_idx} is ready")
        logger.info(f"  Deployer DID: {deployer_did}")
        logger.info(f"  User DID: {user_did}")

    logger.info(f"\n✓ All {non_quorum_count} non-quorum nodes are ready")


def main():
    """Main setup function."""
    args = parse_arguments()

    try:
        # Load configuration
        config = load_config(args.config)

        # Override log level if specified
        if args.log_level:
            config.logging.level = args.log_level

        # Initialize path manager
        paths = PathManager(config.paths.workspace)

        # Clean mode - remove everything
        if args.clean:
            print("🧹 Clean mode - removing all existing data...")
            if paths.workspace.exists():
                import shutil
                shutil.rmtree(paths.workspace)
            paths.ensure_directories()

        # Ensure directories exist
        paths.ensure_directories()

        # Setup logging
        logger = setup_logger(
            log_dir=config.paths.logs,
            log_level=config.logging.level,
            log_format=config.logging.format,
            file_enabled=config.logging.file_enabled,
            console_enabled=config.logging.console_enabled
        )

        logger.info("=" * 70)
        logger.info("RUBIX TESTNET SETUP")
        logger.info("=" * 70)
        logger.info(f"Configuration: {config.config_path}")
        logger.info(f"Workspace: {paths.workspace}")
        logger.info(f"Platform: {paths.platform.os_name} ({paths.platform.archive_suffix})")
        logger.info(f"Quorum nodes: {config.quorum_nodes.count}")
        logger.info(f"Non-quorum nodes: {config.non_quorum_nodes.count}")
        logger.info("=" * 70)

        # Initialize state manager
        state = InstallationState(paths.state_file)

        # Initialize password manager
        password_mgr = PasswordManager(config)

        # PHASE 1: Installation
        if not args.skip_install:
            installer = RubixInstaller(paths, config, state)
            installer.install_all(force=args.force)

            # Verify installation
            if not installer.verify_installation():
                logger.error("Installation verification failed!")
                return 1
        else:
            logger.info("Skipping installation phase (--skip-install)")

        # PHASE 2: Node Setup
        node_mgr = RubixNodeManager(paths, config, state, password_mgr)

        # Setup quorum nodes
        quorum_dids = setup_quorum_nodes(node_mgr, config, paths)

        # Setup non-quorum nodes
        setup_non_quorum_nodes(node_mgr, config, paths, quorum_dids)

        # Success!
        log_section("Setup Complete!")
        logger.info("✅ All nodes are running and configured")
        logger.info(f"\nQuorum nodes: {config.quorum_nodes.count} (ports {config.quorum_nodes.start_port}-{config.quorum_nodes.start_port + config.quorum_nodes.count - 1})")
        logger.info(f"Non-quorum nodes: {config.non_quorum_nodes.count} (ports {config.non_quorum_nodes.start_port}-{config.non_quorum_nodes.start_port + config.non_quorum_nodes.count - 1})")
        logger.info(f"\nLogs: {config.paths.logs}")
        logger.info(f"State: {paths.state_file}")

        return 0

    except RubixError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
