"""Custom exceptions for Rubix testnet scripts."""


class RubixError(Exception):
    """Base exception for all Rubix-related errors."""
    pass


class ConfigurationError(RubixError):
    """Raised when there's a configuration error."""
    pass


class DependencyError(RubixError):
    """Raised when a required dependency is missing or invalid."""

    def __init__(self, dependency: str, message: str = ""):
        self.dependency = dependency
        msg = f"Dependency '{dependency}' error"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class NodeError(RubixError):
    """Base exception for node-related errors."""

    def __init__(self, node_idx: int, message: str):
        self.node_idx = node_idx
        super().__init__(f"Node {node_idx}: {message}")


class NodeStartupError(NodeError):
    """Raised when a node fails to start."""

    def __init__(self, node_idx: int, reason: str):
        super().__init__(node_idx, f"Failed to start: {reason}")


class NodeHealthCheckError(NodeError):
    """Raised when a node health check fails."""

    def __init__(self, node_idx: int, port: int, reason: str = ""):
        msg = f"Health check failed on port {port}"
        if reason:
            msg += f": {reason}"
        super().__init__(node_idx, msg)


class NodeCommunicationError(NodeError):
    """Raised when communication with a node fails."""

    def __init__(self, node_idx: int, endpoint: str, reason: str = ""):
        msg = f"Communication failed with endpoint '{endpoint}'"
        if reason:
            msg += f": {reason}"
        super().__init__(node_idx, msg)


class DIDError(RubixError):
    """Base exception for DID-related errors."""
    pass


class DIDCreationError(DIDError):
    """Raised when DID creation fails."""

    def __init__(self, node_idx: int, reason: str = ""):
        self.node_idx = node_idx
        msg = f"Failed to create DID on node {node_idx}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class DIDRegistrationError(DIDError):
    """Raised when DID registration fails."""

    def __init__(self, did: str, reason: str = ""):
        self.did = did
        msg = f"Failed to register DID {did}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class CommandError(RubixError):
    """Raised when a command execution fails."""

    def __init__(self, command: str, exit_code: int, stderr: str = ""):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr

        msg = f"Command failed with exit code {exit_code}: {command}"
        if stderr:
            # Truncate stderr if too long
            stderr_preview = stderr[:200] + "..." if len(stderr) > 200 else stderr
            msg += f"\nStderr: {stderr_preview}"

        super().__init__(msg)


class DownloadError(RubixError):
    """Raised when a download fails."""

    def __init__(self, url: str, reason: str = ""):
        self.url = url
        msg = f"Failed to download from {url}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class ValidationError(RubixError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: any, reason: str):
        self.field = field
        self.value = value
        msg = f"Validation failed for '{field}' with value '{value}': {reason}"
        super().__init__(msg)


class PortInUseError(RubixError):
    """Raised when attempting to use a port that's already in use."""

    def __init__(self, port: int, process_info: str = ""):
        self.port = port
        msg = f"Port {port} is already in use"
        if process_info:
            msg += f" by {process_info}"
        super().__init__(msg)


class TimeoutError(RubixError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Operation '{operation}' timed out after {timeout_seconds} seconds")


class StateError(RubixError):
    """Raised when there's an issue with state management."""
    pass
