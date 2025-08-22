"""Configuration management for DomainTools client."""

import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError


class DomainToolsConfig(BaseModel):
    """Configuration model for DomainTools API."""

    api_key: str = Field(..., description="DomainTools API key")
    api_secret: SecretStr = Field(..., description="DomainTools API secret")
    api_url: Optional[str] = Field(None, description="Custom API URL")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    output_format: str = Field("json", description="Default output format (json, xml, html)")

    class Config:
        """Configuration for the DomainToolsConfig model."""

        json_encoders = {SecretStr: lambda v: v.get_secret_value() if v else None}


class ConfigManager:
    """Manages configuration for DomainTools client."""

    DEFAULT_CONFIG_DIR = Path.home() / ".domaintools"
    DEFAULT_CONFIG_FILE = "config.json"
    ENV_FILE = ".env"
    YAML_CONFIG_FILES = ["config.yaml", "config.yml", "domaintools.yaml", "domaintools.yml"]

    def __init__(self, config_dir: Optional[Path] = None, config_file: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Optional custom configuration directory
            config_file: Optional specific config file to use
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self.yaml_config_file = None
        self.config: Optional[DomainToolsConfig] = None

        # Check for YAML config files in current directory
        for yaml_file in self.YAML_CONFIG_FILES:
            if Path(yaml_file).exists():
                self.yaml_config_file = Path(yaml_file)
                break

        # Override with specific config file if provided
        if config_file and Path(config_file).exists():
            self.yaml_config_file = Path(config_file)

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load environment variables
        load_dotenv(self.ENV_FILE)
        load_dotenv(self.config_dir / self.ENV_FILE)

    def load(self) -> DomainToolsConfig:
        """Load configuration from various sources.

        Priority order:
        1. Environment variables
        2. YAML config file (if exists)
        3. JSON config file (if exists)
        4. Default values

        Returns:
            Loaded configuration
        """
        config_data = {}

        # Load from YAML config file if it exists
        if self.yaml_config_file and self.yaml_config_file.exists():
            try:
                with open(self.yaml_config_file) as f:
                    yaml_data = yaml.safe_load(f)
                    if yaml_data:
                        # Extract API configuration
                        if "api" in yaml_data:
                            config_data["api_key"] = yaml_data["api"].get("key")
                            config_data["api_secret"] = yaml_data["api"].get("secret")
                            config_data["api_url"] = yaml_data["api"].get("url")

                        # Extract settings
                        if "settings" in yaml_data:
                            config_data["timeout"] = yaml_data["settings"].get("timeout", 30)
                            config_data["max_retries"] = yaml_data["settings"].get("max_retries", 3)
                            config_data["output_format"] = yaml_data["settings"].get(
                                "output_format", "table"
                            )
            except (OSError, yaml.YAMLError) as e:
                print(f"Warning: Error reading YAML config: {e}")

        # Load from JSON config file if it exists and no YAML was loaded
        elif self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                pass

        # Override with environment variables
        env_mappings = {
            "DOMAINTOOLS_API_KEY": "api_key",
            "DOMAINTOOLS_API_SECRET": "api_secret",
            "DOMAINTOOLS_API_URL": "api_url",
            "DOMAINTOOLS_TIMEOUT": "timeout",
            "DOMAINTOOLS_MAX_RETRIES": "max_retries",
            "DOMAINTOOLS_OUTPUT_FORMAT": "output_format",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if config_key in ["timeout", "max_retries"]:
                    try:
                        config_data[config_key] = int(value)
                    except ValueError:
                        pass
                else:
                    config_data[config_key] = value

        # Validate and create config
        try:
            self.config = DomainToolsConfig(**config_data)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

        return self.config

    def save(self, config: Optional[DomainToolsConfig] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save (uses current if not provided)
        """
        if config:
            self.config = config

        if not self.config:
            raise ValueError("No configuration to save")

        # Convert to dict and handle SecretStr
        config_dict = self.config.model_dump()
        if "api_secret" in config_dict and hasattr(config_dict["api_secret"], "get_secret_value"):
            config_dict["api_secret"] = config_dict["api_secret"].get_secret_value()

        with open(self.config_file, "w") as f:
            json.dump(config_dict, f, indent=2)

        # Set file permissions to be readable only by owner
        self.config_file.chmod(0o600)

    def update(self, **kwargs) -> DomainToolsConfig:
        """Update configuration with new values.

        Args:
            **kwargs: Configuration values to update

        Returns:
            Updated configuration
        """
        if not self.config:
            self.load()

        if self.config is None:
            raise ValueError("No configuration to update")

        config_dict = self.config.model_dump()
        config_dict.update(kwargs)

        self.config = DomainToolsConfig(**config_dict)
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if not self.config:
            self.load()

        return getattr(self.config, key, default)

    def is_configured(self) -> bool:
        """Check if API credentials are configured.

        Returns:
            True if configured, False otherwise
        """
        try:
            config = self.load()
            return bool(config.api_key and config.api_secret)
        except (ValueError, ValidationError):
            return False

    def clear(self) -> None:
        """Clear saved configuration."""
        if self.config_file.exists():
            self.config_file.unlink()
        self.config = None

    def get_client(self):
        """Get a configured DomainTools client.

        Returns:
            Configured DomainToolsClient instance
        """
        from ..api.client import DomainToolsClient

        if not self.config:
            self.load()

        if not self.config:
            raise ValueError("No configuration available")

        return DomainToolsClient(
            api_key=self.config.api_key,
            api_secret=self.config.api_secret.get_secret_value(),
            api_url=self.config.api_url,
        )
