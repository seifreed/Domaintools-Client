"""Tests for configuration management."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from domaintools_client.config.manager import ConfigManager, DomainToolsConfig


class TestDomainToolsConfig:
    """Test the DomainToolsConfig model."""

    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = DomainToolsConfig(
            api_key="test_key", api_secret="test_secret", timeout=30, max_retries=3
        )
        assert config.api_key == "test_key"
        assert config.api_secret.get_secret_value() == "test_secret"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.output_format == "json"  # default value

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        with pytest.raises(ValidationError):
            DomainToolsConfig()

    def test_invalid_types(self):
        """Test validation with invalid field types."""
        with pytest.raises(ValidationError):
            DomainToolsConfig(
                api_key="test_key",
                api_secret="test_secret",
                timeout="invalid",  # should be int
                max_retries=3,
            )


class TestConfigManager:
    """Test the ConfigManager class."""

    def test_init_default(self):
        """Test default initialization."""
        manager = ConfigManager()
        assert manager.config_dir == Path.home() / ".domaintools"
        assert manager.config_file == manager.config_dir / "config.json"

    def test_init_custom_dir(self, temp_config_dir):
        """Test initialization with custom directory."""
        manager = ConfigManager(config_dir=temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "config.json"

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "env_key", "DOMAINTOOLS_API_SECRET": "env_secret"}
    )
    def test_load_from_environment(self, temp_config_dir):
        """Test loading configuration from environment variables."""
        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        assert config.api_key == "env_key"
        assert config.api_secret.get_secret_value() == "env_secret"

    def test_load_from_yaml_file(self, temp_config_dir):
        """Test loading configuration from YAML file."""
        yaml_content = {
            "api": {"key": "yaml_key", "secret": "yaml_secret"},
            "settings": {"timeout": 60, "max_retries": 5},
        }

        yaml_file = temp_config_dir / "config.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_content, f)

        manager = ConfigManager(config_dir=temp_config_dir, config_file=str(yaml_file))
        config = manager.load()

        assert config.api_key == "yaml_key"
        assert config.api_secret.get_secret_value() == "yaml_secret"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_load_from_json_file(self, temp_config_dir):
        """Test loading configuration from JSON file."""
        json_content = {"api_key": "json_key", "api_secret": "json_secret", "timeout": 45}

        json_file = temp_config_dir / "config.json"
        with open(json_file, "w") as f:
            json.dump(json_content, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        assert config.api_key == "json_key"
        assert config.api_secret.get_secret_value() == "json_secret"
        assert config.timeout == 45

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "env_key", "DOMAINTOOLS_API_SECRET": "env_secret"}
    )
    def test_environment_overrides_file(self, temp_config_dir):
        """Test that environment variables override file configuration."""
        json_content = {"api_key": "file_key", "api_secret": "file_secret"}

        json_file = temp_config_dir / "config.json"
        with open(json_file, "w") as f:
            json.dump(json_content, f)

        manager = ConfigManager(config_dir=temp_config_dir)
        config = manager.load()

        # Environment should override file
        assert config.api_key == "env_key"
        assert config.api_secret.get_secret_value() == "env_secret"

    def test_save_config(self, temp_config_dir):
        """Test saving configuration to file."""
        config = DomainToolsConfig(api_key="save_key", api_secret="save_secret", timeout=30)

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.save(config)

        # Verify file was created
        assert manager.config_file.exists()

        # Verify content
        with open(manager.config_file) as f:
            saved_data = json.load(f)

        assert saved_data["api_key"] == "save_key"
        assert saved_data["api_secret"] == "save_secret"
        assert saved_data["timeout"] == 30

    def test_update_config(self, temp_config_dir):
        """Test updating configuration."""
        manager = ConfigManager(config_dir=temp_config_dir)

        # Load initial config with environment
        with patch.dict(
            os.environ,
            {"DOMAINTOOLS_API_KEY": "initial_key", "DOMAINTOOLS_API_SECRET": "initial_secret"},
        ):
            manager.load()

        # Update config
        updated_config = manager.update(timeout=120, max_retries=10)

        assert updated_config.api_key == "initial_key"
        assert updated_config.timeout == 120
        assert updated_config.max_retries == 10

    def test_get_config_value(self, temp_config_dir):
        """Test getting configuration values."""
        with patch.dict(
            os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
        ):
            manager = ConfigManager(config_dir=temp_config_dir)

            assert manager.get("api_key") == "test_key"
            assert manager.get("timeout") == 30  # default value
            assert manager.get("nonexistent", "default") == "default"

    def test_is_configured_true(self, temp_config_dir):
        """Test is_configured returns True when credentials are set."""
        with patch.dict(
            os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
        ):
            manager = ConfigManager(config_dir=temp_config_dir)
            assert manager.is_configured() is True

    def test_is_configured_false(self, temp_config_dir):
        """Test is_configured returns False when credentials are missing."""
        manager = ConfigManager(config_dir=temp_config_dir)
        assert manager.is_configured() is False

    def test_clear_config(self, temp_config_dir):
        """Test clearing configuration."""
        # Create a config file
        config_file = temp_config_dir / "config.json"
        config_file.write_text('{"api_key": "test"}')

        manager = ConfigManager(config_dir=temp_config_dir)
        manager.clear()

        assert not config_file.exists()
        assert manager.config is None

    def test_get_client(self, temp_config_dir):
        """Test getting a configured client."""
        with patch.dict(
            os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
        ):
            manager = ConfigManager(config_dir=temp_config_dir)

            with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client:
                _ = manager.get_client()
                mock_client.assert_called_once_with(
                    api_key="test_key", api_secret="test_secret", api_url=None
                )

    def test_invalid_yaml_file_handling(self, temp_config_dir):
        """Test handling of invalid YAML files."""
        yaml_file = temp_config_dir / "config.yaml"
        yaml_file.write_text("invalid: yaml: content:")

        manager = ConfigManager(config_dir=temp_config_dir, config_file=str(yaml_file))

        # Should handle error gracefully and not crash
        with patch("builtins.print") as mock_print:
            _ = manager.load()
            # Should print warning about invalid YAML
            mock_print.assert_called()

    def test_invalid_json_file_handling(self, temp_config_dir):
        """Test handling of invalid JSON files."""
        json_file = temp_config_dir / "config.json"
        json_file.write_text('{"invalid": json content}')

        manager = ConfigManager(config_dir=temp_config_dir)

        # Should handle error gracefully and not crash
        _ = manager.load()  # Should not raise exception
