#!/usr/bin/env python3
"""
Rubix Testnet Restart Script (Refactored)

Restarts nodes that were previously set up.
"""

import sys
import json
import argparse

from config_loader import load_config
from path_manager import PathManager
from state_manager import InstallationState
from logger import setup_logger, get_logger, log_section
from security import PasswordManager
from node_manager import RubixNodeManager
from exceptions import RubixError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Restart Rubix testnet nodes",
        epilog="""
Examples:
  # Restart all nodes
  python restart_nodes.py

  # Restart with debug logging
  python restart_nodes.py --log-level DEBUG
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Override log level from config'
    )

    return parser.parse_args()


def main():
    """Main restart function."""
    args = parse_arguments()

    try:
        # Load configuration
        config = load_config(args.config)

        # Override log level if specified
        if args.log_level:
            config.logging.level = args.log_level

        # Initialize path manager
        paths = PathManager(config.paths.workspace)
        paths.ensure_directories()

        # Setup logging
        logger = setup_logger(
            log_dir=config.paths.logs,
            log_level=config.logging.level,
            log_format=config.logging.format,
            file_enabled=config.logging.file_enabled,
            console_enabled=config.logging.console_enabled
        )

        log_section("Restarting Rubix Nodes")

        # Initialize state manager
        state = InstallationState(paths.state_file)

        # Check if installation is complete
        if not state.is_installation_complete():
            logger.error("Installation is not complete. Run setup.py first.")
            return 1

        # Check if quorum list exists
        if not paths.quorum_list.exists():
            logger.error(f"Quorum list not found at {paths.quorum_list}")
            logger.error("Run setup.py first to initialize nodes.")
            return 1

        # Initialize managers
        password_mgr = PasswordManager(config)
        node_mgr = RubixNodeManager(paths, config, state, password_mgr)

        # Restart quorum nodes
        quorum_count = config.quorum_nodes.count
        logger.info(f"Restarting {quorum_count} quorum nodes...")

        for i in range(quorum_count):
            logger.info(f"\nRestarting quorum node {i}...")
            node_mgr.start_node(i)

        # Restart non-quorum nodes
        non_quorum_count = config.non_quorum_nodes.count
        logger.info(f"\nRestarting {non_quorum_count} non-quorum nodes...")

        for i in range(non_quorum_count):
            node_idx = quorum_count + i
            logger.info(f"\nRestarting non-quorum node {node_idx}...")
            node_mgr.start_node(node_idx)

        # Re-setup quorums
        logger.info("\nRe-configuring quorums...")

        # Load quorum list
        with open(paths.quorum_list, 'r') as f:
            quorum_list = json.load(f)

        # Setup each quorum
        for i in range(quorum_count):
            quorum_did = quorum_list[i]["address"]
            node_mgr.setup_quorum(i, quorum_did)

        # Success!
        log_section("Restart Complete!")
        logger.info("✅ All nodes restarted successfully")
        logger.info(f"\nQuorum nodes: {quorum_count} (ports {config.quorum_nodes.start_port}-{config.quorum_nodes.start_port + quorum_count - 1})")
        logger.info(f"Non-quorum nodes: {non_quorum_count} (ports {config.non_quorum_nodes.start_port}-{config.non_quorum_nodes.start_port + non_quorum_count - 1})")

        return 0

    except RubixError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Restart interrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
