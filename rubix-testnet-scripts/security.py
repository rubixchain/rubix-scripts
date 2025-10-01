"""Security utilities for Rubix testnet scripts."""

import os
import getpass
from typing import Optional
from logger import get_logger
from config_loader import Config


def get_password(
    password_type: str,
    config: Config,
    prompt: Optional[str] = None
) -> str:
    """
    Get password from environment variable or prompt user.

    Args:
        password_type: Type of password ('priv_pwd' or 'quorum_pwd')
        config: Configuration object
        prompt: Custom prompt message (optional)

    Returns:
        Password string

    Raises:
        ValueError: If password_type is invalid
    """
    logger = get_logger()

    if password_type not in ['priv_pwd', 'quorum_pwd']:
        raise ValueError(f"Invalid password type: {password_type}")

    # Try to get from environment variable
    env_var = config.security.password_env_vars.get(password_type)
    if env_var:
        pwd = os.getenv(env_var)
        if pwd:
            logger.debug(f"Using password from environment variable: {env_var}")
            return pwd

    # Check if default passwords are allowed
    if config.security.allow_default_passwords:
        default_pwd = config.security.default_passwords.get(password_type)
        if default_pwd:
            logger.warning(
                f"Using default {password_type} - NOT RECOMMENDED FOR PRODUCTION!"
            )
            return default_pwd

    # Prompt user for password
    if prompt is None:
        prompt = f"Enter {password_type.replace('_', ' ')}: "

    pwd = getpass.getpass(prompt)

    if not pwd:
        logger.warning(f"Empty password provided for {password_type}")

    return pwd


def get_priv_password(config: Config) -> str:
    """
    Get private key password.

    Args:
        config: Configuration object

    Returns:
        Password string
    """
    return get_password('priv_pwd', config, "Enter private key password: ")


def get_quorum_password(config: Config) -> str:
    """
    Get quorum password.

    Args:
        config: Configuration object

    Returns:
        Password string
    """
    return get_password('quorum_pwd', config, "Enter quorum password: ")


class PasswordManager:
    """Manages passwords for multiple operations."""

    def __init__(self, config: Config):
        """
        Initialize password manager.

        Args:
            config: Configuration object
        """
        self.config = config
        self._priv_pwd: Optional[str] = None
        self._quorum_pwd: Optional[str] = None

    def get_priv_password(self) -> str:
        """Get private key password (cached after first retrieval)."""
        if self._priv_pwd is None:
            self._priv_pwd = get_priv_password(self.config)
        return self._priv_pwd

    def get_quorum_password(self) -> str:
        """Get quorum password (cached after first retrieval)."""
        if self._quorum_pwd is None:
            self._quorum_pwd = get_quorum_password(self.config)
        return self._quorum_pwd

    def clear(self) -> None:
        """Clear cached passwords."""
        self._priv_pwd = None
        self._quorum_pwd = None
