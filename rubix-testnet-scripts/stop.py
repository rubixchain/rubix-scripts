#!/usr/bin/env python3
"""
Rubix Testnet Stop Script (Refactored)

Gracefully stops all running Rubix nodes.
"""

import sys
import argparse

from config_loader import load_config
from path_manager import PathManager
from state_manager import InstallationState, NodeStatus
from logger import setup_logger, get_logger, log_section
from security import PasswordManager
from node_manager import RubixNodeManager
from exceptions import RubixError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Stop Rubix testnet nodes",
        epilog="""
Examples:
  # Stop all nodes
  python stop.py

  # Stop specific node
  python stop.py --node 0

  # Stop range of nodes
  python stop.py --start 0 --end 4
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--node',
        type=int,
        help='Stop specific node index'
    )

    parser.add_argument(
        '--start',
        type=int,
        help='Start node index (inclusive)'
    )

    parser.add_argument(
        '--end',
        type=int,
        help='End node index (inclusive)'
    )

    return parser.parse_args()


def main():
    """Main stop function."""
    args = parse_arguments()

    try:
        # Load configuration
        config = load_config(args.config)

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

        log_section("Stopping Rubix Nodes")

        # Initialize state manager
        state = InstallationState(paths.state_file)

        # Initialize node manager
        password_mgr = PasswordManager(config)
        node_mgr = RubixNodeManager(paths, config, state, password_mgr)

        # Determine which nodes to stop
        total_nodes = config.get_total_node_count()

        if args.node is not None:
            # Stop specific node
            nodes_to_stop = [args.node]
        elif args.start is not None and args.end is not None:
            # Stop range
            nodes_to_stop = list(range(args.start, args.end + 1))
        else:
            # Stop all nodes
            nodes_to_stop = list(range(total_nodes))

        logger.info(f"Stopping {len(nodes_to_stop)} node(s)...")

        # Stop each node
        stopped_count = 0
        failed_count = 0

        for node_idx in nodes_to_stop:
            if node_idx >= total_nodes:
                logger.warning(f"Node {node_idx} does not exist (max: {total_nodes - 1})")
                continue

            try:
                node_mgr.stop_node(node_idx)
                stopped_count += 1
            except Exception as e:
                logger.error(f"Failed to stop node {node_idx}: {e}")
                failed_count += 1

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("STOP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Stopped: {stopped_count}")
        logger.info(f"Failed: {failed_count}")

        if failed_count == 0:
            logger.info("\n✅ All nodes stopped successfully")
            return 0
        else:
            logger.warning(f"\n⚠️  {failed_count} node(s) failed to stop")
            return 1

    except RubixError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
