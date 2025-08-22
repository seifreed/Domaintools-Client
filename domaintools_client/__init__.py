"""DomainTools Client - A modular CLI and library for DomainTools API."""

__version__ = "0.1.0"
__author__ = "Your Name"

from .api.client import DomainToolsClient
from .config.manager import ConfigManager

__all__ = ["DomainToolsClient", "ConfigManager"]
