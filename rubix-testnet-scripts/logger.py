"""Logging configuration for Rubix testnet scripts."""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(
    log_dir: Path,
    log_level: str = "INFO",
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    file_enabled: bool = True,
    console_enabled: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        file_enabled: Enable file logging
        console_enabled: Enable console logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    global _logger

    # Create logger
    logger = logging.getLogger("rubix")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_enabled:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "rubix-setup.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the global logger instance.

    Returns:
        Logger instance

    Raises:
        RuntimeError: If logger hasn't been initialized
    """
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logger() first.")
    return _logger


class LoggerContext:
    """Context manager for temporary log level changes."""

    def __init__(self, level: str):
        """
        Initialize context manager.

        Args:
            level: Temporary log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.level = level
        self.original_level = None
        self.logger = get_logger()

    def __enter__(self):
        """Enter context - set new log level."""
        self.original_level = self.logger.level
        self.logger.setLevel(getattr(logging, self.level.upper()))
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore original log level."""
        self.logger.setLevel(self.original_level)


def log_section(title: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a section header for better readability.

    Args:
        title: Section title
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    separator = "=" * 60
    logger.info(separator)
    logger.info(f"  {title}")
    logger.info(separator)


def log_step(step_num: int, total_steps: int, description: str,
             logger: Optional[logging.Logger] = None) -> None:
    """
    Log a step in a multi-step process.

    Args:
        step_num: Current step number
        total_steps: Total number of steps
        description: Step description
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    logger.info(f"[Step {step_num}/{total_steps}] {description}")


def log_node_info(node_idx: int, message: str,
                  logger: Optional[logging.Logger] = None) -> None:
    """
    Log a message specific to a node.

    Args:
        node_idx: Node index
        message: Log message
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    logger.info(f"[Node {node_idx}] {message}")


def log_command(command: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a command being executed.

    Args:
        command: Command string
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    # If command is a list, join it for display
    if isinstance(command, list):
        command = " ".join(command)

    logger.debug(f"Executing: {command}")


def log_command_output(stdout: str, stderr: str,
                       logger: Optional[logging.Logger] = None) -> None:
    """
    Log command output.

    Args:
        stdout: Standard output
        stderr: Standard error
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    if stdout:
        for line in stdout.strip().split('\n'):
            if line:
                logger.debug(f"  stdout: {line}")

    if stderr:
        for line in stderr.strip().split('\n'):
            if line:
                logger.debug(f"  stderr: {line}")
