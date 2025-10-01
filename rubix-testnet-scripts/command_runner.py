"""Secure command execution utilities."""

import subprocess
from typing import List, Optional, Union
from dataclasses import dataclass
from logger import get_logger, log_command, log_command_output
from exceptions import CommandError, TimeoutError as RubixTimeoutError


@dataclass
class CommandResult:
    """Result from command execution."""
    stdout: str
    stderr: str
    exit_code: int
    command: List[str]

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.exit_code == 0

    @property
    def has_error_markers(self) -> bool:
        """Check if output contains error markers."""
        error_patterns = ['[ERROR]', 'parse error', 'Error:', 'error:']
        combined_output = self.stdout + self.stderr

        return any(pattern in combined_output for pattern in error_patterns)


def run_command(
    cmd: Union[List[str], str],
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    check: bool = True,
    capture_output: bool = True
) -> CommandResult:
    """
    Execute a command safely.

    Args:
        cmd: Command to execute (list of arguments or string)
        timeout: Timeout in seconds (None for no timeout)
        cwd: Working directory for command execution
        env: Environment variables
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr

    Returns:
        CommandResult object

    Raises:
        CommandError: If command fails and check=True
        TimeoutError: If command times out
        ValueError: If cmd is a string (shell commands not allowed)
    """
    logger = get_logger()

    # Ensure command is a list (no shell=True for security)
    if isinstance(cmd, str):
        raise ValueError(
            "Command must be a list of arguments. "
            "Shell commands are not allowed for security reasons."
        )

    log_command(cmd, logger)

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            cwd=cwd,
            env=env,
            timeout=timeout,
            text=True,
            check=False  # We handle errors manually
        )

        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""

        # Log output at debug level
        if capture_output:
            log_command_output(stdout, stderr, logger)

        cmd_result = CommandResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=result.returncode,
            command=cmd
        )

        # Check for errors
        if check and (result.returncode != 0 or cmd_result.has_error_markers):
            raise CommandError(
                command=" ".join(cmd),
                exit_code=result.returncode,
                stderr=stderr
            )

        return cmd_result

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        raise RubixTimeoutError(
            operation=" ".join(cmd),
            timeout_seconds=timeout
        )
    except FileNotFoundError as e:
        logger.error(f"Command not found: {cmd[0]}")
        raise CommandError(
            command=" ".join(cmd),
            exit_code=-1,
            stderr=f"Command not found: {cmd[0]}"
        )


def run_command_with_retry(
    cmd: Union[List[str], str],
    max_attempts: int = 3,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    retry_delay: int = 2
) -> CommandResult:
    """
    Execute a command with automatic retry on failure.

    Args:
        cmd: Command to execute
        max_attempts: Maximum number of attempts
        timeout: Timeout in seconds per attempt
        cwd: Working directory
        retry_delay: Delay between retries in seconds

    Returns:
        CommandResult object

    Raises:
        CommandError: If all attempts fail
    """
    import time
    logger = get_logger()

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_attempts} for command: {cmd}")
            return run_command(cmd, timeout=timeout, cwd=cwd, check=True)
        except CommandError as e:
            last_error = e
            if attempt < max_attempts:
                logger.warning(f"Attempt {attempt} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"All {max_attempts} attempts failed")

    # If we get here, all attempts failed
    raise last_error
