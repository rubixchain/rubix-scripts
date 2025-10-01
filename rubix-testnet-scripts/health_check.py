"""Health checking utilities for Rubix nodes."""

import time
import requests
from typing import Optional
from logger import get_logger, log_node_info
from exceptions import NodeHealthCheckError
from config_loader import Config


def check_node_health(
    port: int,
    node_idx: Optional[int] = None,
    timeout: int = 10
) -> bool:
    """
    Check if a node is healthy by querying its API.

    Args:
        port: Node's HTTP port
        node_idx: Node index (for logging)
        timeout: Request timeout in seconds

    Returns:
        True if node is healthy, False otherwise
    """
    logger = get_logger()
    url = f"http://localhost:{port}/api/getalldid"

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            if node_idx is not None:
                log_node_info(node_idx, f"Health check passed on port {port}", logger)
            return True
        else:
            if node_idx is not None:
                log_node_info(
                    node_idx,
                    f"Health check failed: HTTP {response.status_code}",
                    logger
                )
            return False
    except requests.exceptions.RequestException as e:
        if node_idx is not None:
            logger.debug(f"[Node {node_idx}] Health check error: {str(e)}")
        return False


def wait_for_node_ready(
    port: int,
    node_idx: int,
    config: Config,
    max_attempts: Optional[int] = None,
    interval: Optional[int] = None
) -> bool:
    """
    Wait for a node to become ready with exponential backoff.

    Args:
        port: Node's HTTP port
        node_idx: Node index
        config: Configuration object
        max_attempts: Maximum number of attempts (uses config if None)
        interval: Seconds between attempts (uses config if None)

    Returns:
        True if node became ready, False if timed out

    Raises:
        NodeHealthCheckError: If node doesn't become ready in time
    """
    logger = get_logger()

    if max_attempts is None:
        max_attempts = config.timeouts.max_health_checks
    if interval is None:
        interval = config.timeouts.health_check_interval

    log_node_info(
        node_idx,
        f"Waiting for node to become ready on port {port} "
        f"(max {max_attempts} attempts, {interval}s interval)",
        logger
    )

    for attempt in range(1, max_attempts + 1):
        logger.debug(f"[Node {node_idx}] Health check attempt {attempt}/{max_attempts}")

        if check_node_health(port, node_idx, config.timeouts.http_request):
            elapsed = attempt * interval
            log_node_info(
                node_idx,
                f"Node is ready (took ~{elapsed}s)",
                logger
            )
            return True

        if attempt < max_attempts:
            logger.debug(f"[Node {node_idx}] Not ready yet, waiting {interval}s...")
            time.sleep(interval)

    # All attempts exhausted
    total_time = max_attempts * interval
    logger.error(
        f"[Node {node_idx}] Failed to become ready after {total_time}s "
        f"({max_attempts} attempts)"
    )

    raise NodeHealthCheckError(
        node_idx=node_idx,
        port=port,
        reason=f"Node did not respond after {max_attempts} attempts ({total_time}s)"
    )


def check_multiple_endpoints(
    port: int,
    node_idx: int,
    endpoints: Optional[list[str]] = None,
    timeout: int = 10
) -> dict[str, bool]:
    """
    Check multiple endpoints on a node.

    Args:
        port: Node's HTTP port
        node_idx: Node index
        endpoints: List of endpoint paths (default: common endpoints)
        timeout: Request timeout in seconds

    Returns:
        Dictionary mapping endpoints to health status
    """
    logger = get_logger()

    if endpoints is None:
        endpoints = [
            "/api/getalldid",
            "/api/status",
            "/api/get-peer-id"
        ]

    results = {}

    for endpoint in endpoints:
        url = f"http://localhost:{port}{endpoint}"
        try:
            response = requests.get(url, timeout=timeout)
            results[endpoint] = response.status_code == 200
        except requests.exceptions.RequestException:
            results[endpoint] = False

    # Log summary
    healthy_count = sum(1 for v in results.values() if v)
    log_node_info(
        node_idx,
        f"Endpoint check: {healthy_count}/{len(endpoints)} healthy",
        logger
    )

    return results


def verify_node_process(port: int) -> bool:
    """
    Verify that a process is listening on the given port.

    Args:
        port: Port to check

    Returns:
        True if a process is listening, False otherwise
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            result = sock.connect_ex(('localhost', port))
            return result == 0
        except Exception:
            return False
