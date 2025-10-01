"""Input validation utilities for Rubix testnet scripts."""

import re
import socket
from pathlib import Path
from typing import Union
from urllib.parse import urlparse
from exceptions import ValidationError


def validate_port(port: int, field_name: str = "port") -> int:
    """
    Validate that a port number is in valid range.

    Args:
        port: Port number to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated port number

    Raises:
        ValidationError: If port is invalid
    """
    if not isinstance(port, int):
        raise ValidationError(field_name, port, "Must be an integer")

    if port < 1024 or port > 65535:
        raise ValidationError(
            field_name,
            port,
            "Must be between 1024 and 65535 (privileged ports < 1024 not allowed)"
        )

    return port


def validate_url(url: str, field_name: str = "url", require_https: bool = False) -> str:
    """
    Validate URL format.

    Args:
        url: URL string to validate
        field_name: Name of the field (for error messages)
        require_https: If True, only allow HTTPS URLs

    Returns:
        The validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not isinstance(url, str) or not url:
        raise ValidationError(field_name, url, "Must be a non-empty string")

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(field_name, url, "Invalid URL format")

        if require_https and result.scheme != "https":
            raise ValidationError(field_name, url, "Must use HTTPS protocol")

        return url
    except Exception as e:
        raise ValidationError(field_name, url, f"Invalid URL: {str(e)}")


def validate_did(did: str, field_name: str = "did") -> str:
    """
    Validate DID format.

    Args:
        did: DID string to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated DID

    Raises:
        ValidationError: If DID format is invalid
    """
    if not isinstance(did, str) or not did:
        raise ValidationError(field_name, did, "Must be a non-empty string")

    # DIDs in Rubix typically start with "bafybmi" or "bafymi"
    pattern = r'^bafy[a-z0-9]{40,}$'

    if not re.match(pattern, did):
        raise ValidationError(
            field_name,
            did,
            "Invalid DID format (expected to start with 'bafy' followed by alphanumeric characters)"
        )

    return did


def validate_path_exists(path: Union[str, Path], field_name: str = "path") -> Path:
    """
    Validate that a path exists.

    Args:
        path: Path to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated Path object

    Raises:
        ValidationError: If path doesn't exist
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise ValidationError(field_name, str(path), "Path does not exist")

    return path_obj


def validate_directory(path: Union[str, Path], field_name: str = "directory",
                       create_if_missing: bool = False) -> Path:
    """
    Validate that a path is a directory.

    Args:
        path: Path to validate
        field_name: Name of the field (for error messages)
        create_if_missing: If True, create directory if it doesn't exist

    Returns:
        The validated Path object

    Raises:
        ValidationError: If path exists but is not a directory
    """
    path_obj = Path(path)

    if not path_obj.exists():
        if create_if_missing:
            path_obj.mkdir(parents=True, exist_ok=True)
            return path_obj
        else:
            raise ValidationError(field_name, str(path), "Directory does not exist")

    if not path_obj.is_dir():
        raise ValidationError(field_name, str(path), "Path exists but is not a directory")

    return path_obj


def validate_file_exists(path: Union[str, Path], field_name: str = "file") -> Path:
    """
    Validate that a path is an existing file.

    Args:
        path: Path to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated Path object

    Raises:
        ValidationError: If path doesn't exist or is not a file
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise ValidationError(field_name, str(path), "File does not exist")

    if not path_obj.is_file():
        raise ValidationError(field_name, str(path), "Path exists but is not a file")

    return path_obj


def validate_node_index(node_idx: int, max_nodes: int, field_name: str = "node_index") -> int:
    """
    Validate node index is in valid range.

    Args:
        node_idx: Node index to validate
        max_nodes: Maximum number of nodes
        field_name: Name of the field (for error messages)

    Returns:
        The validated node index

    Raises:
        ValidationError: If node index is invalid
    """
    if not isinstance(node_idx, int):
        raise ValidationError(field_name, node_idx, "Must be an integer")

    if node_idx < 0 or node_idx >= max_nodes:
        raise ValidationError(
            field_name,
            node_idx,
            f"Must be between 0 and {max_nodes - 1}"
        )

    return node_idx


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """
    Check if a port is already in use.

    Args:
        port: Port number to check
        host: Host to check (default: localhost)

    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True


def validate_port_available(port: int, field_name: str = "port") -> int:
    """
    Validate that a port is available (not in use).

    Args:
        port: Port number to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated port number

    Raises:
        ValidationError: If port is in use
    """
    # First validate port range
    validate_port(port, field_name)

    # Then check if in use
    if is_port_in_use(port):
        raise ValidationError(
            field_name,
            port,
            f"Port {port} is already in use"
        )

    return port


def validate_positive_integer(value: int, field_name: str = "value") -> int:
    """
    Validate that a value is a positive integer.

    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated value

    Raises:
        ValidationError: If value is not a positive integer
    """
    if not isinstance(value, int):
        raise ValidationError(field_name, value, "Must be an integer")

    if value <= 0:
        raise ValidationError(field_name, value, "Must be a positive integer")

    return value


def validate_non_negative_integer(value: int, field_name: str = "value") -> int:
    """
    Validate that a value is a non-negative integer.

    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated value

    Raises:
        ValidationError: If value is not a non-negative integer
    """
    if not isinstance(value, int):
        raise ValidationError(field_name, value, "Must be an integer")

    if value < 0:
        raise ValidationError(field_name, value, "Must be a non-negative integer")

    return value
