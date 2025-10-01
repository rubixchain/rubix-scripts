#!/usr/bin/env python3
"""
Test script for the new infrastructure components.
This allows you to test the new modules before full integration.
"""

import sys
from pathlib import Path


def test_config_loader():
    """Test configuration loading."""
    print("\n=== Testing Config Loader ===")
    try:
        from config_loader import load_config, get_config

        config = load_config()

        print(f"✓ Config loaded successfully")
        print(f"  Quorum nodes: {config.quorum_nodes.count}")
        print(f"  Quorum start port: {config.quorum_nodes.start_port}")
        print(f"  Non-quorum nodes: {config.non_quorum_nodes.count}")
        print(f"  Non-quorum start port: {config.non_quorum_nodes.start_port}")
        print(f"  Workspace: {config.paths.workspace}")
        print(f"  Log level: {config.logging.level}")

        # Test port calculation
        print(f"\n  Port calculations:")
        for i in range(config.quorum_nodes.count):
            port = config.get_node_port(i)
            grpc = config.get_node_grpc_port(i)
            print(f"    Quorum Node {i}: HTTP={port}, gRPC={grpc}")

        for i in range(config.non_quorum_nodes.count):
            idx = config.quorum_nodes.count + i
            port = config.get_node_port(idx)
            grpc = config.get_node_grpc_port(idx)
            print(f"    Non-Quorum Node {idx}: HTTP={port}, gRPC={grpc}")

        return True
    except Exception as e:
        print(f"✗ Config loader failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_path_manager():
    """Test path manager."""
    print("\n=== Testing Path Manager ===")
    try:
        from path_manager import PathManager
        from config_loader import get_config

        config = get_config()
        pm = PathManager(config.paths.workspace)

        print(f"✓ Path manager initialized")
        print(f"  Platform: {pm.platform.os_name}")
        print(f"  Architecture: {pm.platform.archive_suffix}")
        print(f"  Build folder: {pm.platform.build_folder}")
        print(f"  Workspace: {pm.workspace}")
        print(f"  Binaries: {pm.binaries}")
        print(f"  Build dir: {pm.build_dir}")
        print(f"  Rubix binary: {pm.rubix_binary}")
        print(f"  IPFS binary: {pm.ipfs_binary}")
        print(f"  Is Windows: {pm.is_windows()}")
        print(f"  Is Mac: {pm.is_mac()}")
        print(f"  Is Linux: {pm.is_linux()}")

        # Test IPFS download URL
        ipfs_url = pm.get_ipfs_download_url("v0.21.0")
        print(f"  IPFS download URL: {ipfs_url}")

        return True
    except Exception as e:
        print(f"✗ Path manager failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_manager():
    """Test state manager."""
    print("\n=== Testing State Manager ===")
    try:
        from state_manager import InstallationState, NodeStatus
        from config_loader import get_config

        config = get_config()
        state_file = config.paths.workspace / ".rubix-state-test.json"

        # Clean up any existing test state
        if state_file.exists():
            state_file.unlink()

        state = InstallationState(state_file)

        print(f"✓ State manager initialized")
        print(f"  State file: {state_file}")

        # Test installation state
        print(f"\nTesting installation state tracking:")
        print(f"  Initially: rubixgoplatform cloned = {state.is_rubixgoplatform_cloned()}")
        state.set_rubixgoplatform_cloned(True)
        print(f"  After set: rubixgoplatform cloned = {state.is_rubixgoplatform_cloned()}")

        # Test node state
        print(f"\nTesting node state tracking:")
        state.set_node_status(0, NodeStatus.RUNNING)
        state.set_node_info(0, pid=12345, did="bafybmi123456", port=20000, grpc_port=10500)

        node_state = state.get_node_state(0)
        print(f"  Node 0 status: {node_state['status']}")
        print(f"  Node 0 DID: {node_state['did']}")
        print(f"  Node 0 port: {node_state['port']}")

        # Get summary
        print(f"\n{state.get_state_summary()}")

        # Clean up
        state_file.unlink()

        return True
    except Exception as e:
        print(f"✗ State manager failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger():
    """Test logging system."""
    print("\n=== Testing Logger ===")
    try:
        from logger import setup_logger, get_logger, log_section, log_step, log_node_info
        from config_loader import get_config

        config = get_config()

        # Setup logger
        logger = setup_logger(
            log_dir=config.paths.logs,
            log_level=config.logging.level,
            file_enabled=config.logging.file_enabled,
            console_enabled=config.logging.console_enabled
        )

        print(f"✓ Logger initialized")

        # Test logging
        log_section("Test Section", logger)
        log_step(1, 5, "Testing step logging", logger)
        log_node_info(0, "Test node message", logger)
        logger.info("Regular info message")
        logger.debug("Debug message (may not appear if level=INFO)")

        print(f"  Log file: {config.paths.logs / 'rubix-setup.log'}")

        return True
    except Exception as e:
        print(f"✗ Logger failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validators():
    """Test input validators."""
    print("\n=== Testing Validators ===")
    try:
        from validators import (
            validate_port, validate_url, validate_did,
            validate_positive_integer, is_port_in_use
        )
        from exceptions import ValidationError

        print(f"✓ Validators imported")

        # Test valid inputs
        print(f"\nTesting valid inputs:")
        validate_port(20000)
        print(f"  ✓ Port 20000 is valid")

        validate_url("https://github.com/rubixchain/rubixgoplatform.git")
        print(f"  ✓ URL is valid")

        validate_did("bafybmi1234567890abcdefghijklmnopqrstuvwxyz")
        print(f"  ✓ DID is valid")

        validate_positive_integer(5)
        print(f"  ✓ Positive integer is valid")

        # Test invalid inputs
        print(f"\nTesting invalid inputs (should catch errors):")

        try:
            validate_port(100)
            print(f"  ✗ Should have caught invalid port")
        except ValidationError as e:
            print(f"  ✓ Caught invalid port: {e}")

        try:
            validate_did("invalid-did")
            print(f"  ✗ Should have caught invalid DID")
        except ValidationError as e:
            print(f"  ✓ Caught invalid DID: {e}")

        # Test port availability
        print(f"\nTesting port availability:")
        print(f"  Port 20000 in use: {is_port_in_use(20000)}")
        print(f"  Port 65534 in use: {is_port_in_use(65534)}")

        return True
    except Exception as e:
        print(f"✗ Validators failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security():
    """Test security module."""
    print("\n=== Testing Security ===")
    try:
        from security import PasswordManager
        from config_loader import get_config

        config = get_config()

        print(f"✓ Security module imported")
        print(f"  Allow default passwords: {config.security.allow_default_passwords}")

        if config.security.allow_default_passwords:
            pm = PasswordManager(config)
            priv_pwd = pm.get_priv_password()
            print(f"  ✓ Got private password: {'*' * len(priv_pwd)}")

            quorum_pwd = pm.get_quorum_password()
            print(f"  ✓ Got quorum password: {'*' * len(quorum_pwd)}")
        else:
            print(f"  ⚠ Default passwords disabled - would prompt user")

        return True
    except Exception as e:
        print(f"✗ Security failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_command_runner():
    """Test command runner."""
    print("\n=== Testing Command Runner ===")
    try:
        from command_runner import run_command, CommandResult

        print(f"✓ Command runner imported")

        # Test simple command
        result = run_command(["echo", "Hello, Rubix!"])
        print(f"  ✓ Command executed")
        print(f"    Exit code: {result.exit_code}")
        print(f"    Output: {result.stdout.strip()}")
        print(f"    Success: {result.success}")

        # Test with list vs string enforcement
        try:
            run_command("echo test")
            print(f"  ✗ Should have rejected string command")
        except ValueError as e:
            print(f"  ✓ Correctly rejected shell command: {e}")

        return True
    except Exception as e:
        print(f"✗ Command runner failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_check():
    """Test health check module."""
    print("\n=== Testing Health Check ===")
    try:
        from health_check import check_node_health, verify_node_process

        print(f"✓ Health check module imported")

        # Test checking a non-existent node
        print(f"\nTesting health check on non-existent node (port 65432):")
        is_healthy = check_node_health(65432, node_idx=999, timeout=2)
        print(f"  Node healthy: {is_healthy} (expected: False)")

        # Test process verification
        print(f"\nTesting process verification:")
        has_process = verify_node_process(65432)
        print(f"  Process listening: {has_process} (expected: False)")

        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("RUBIX NEW INFRASTRUCTURE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Config Loader", test_config_loader),
        ("Path Manager", test_path_manager),
        ("State Manager", test_state_manager),
        ("Logger", test_logger),
        ("Validators", test_validators),
        ("Security", test_security),
        ("Command Runner", test_command_runner),
        ("Health Check", test_health_check),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
