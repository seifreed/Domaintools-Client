"""Integration tests for CLI functionality."""

import os
from unittest.mock import Mock, patch

from click.testing import CliRunner

from domaintools_client.cli.main import cli


class TestCLIIntegration:
    """Test CLI integration functionality."""

    def test_cli_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "DomainTools CLI version" in result.output

    def test_cli_help(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "DomainTools CLI" in result.output
        assert "domain" in result.output
        assert "config" in result.output

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
    )
    def test_config_show_with_credentials(self):
        """Test config show command with credentials."""
        runner = CliRunner()

        with patch("domaintools_client.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_config = Mock()
            mock_config.api_key = "test_key"
            mock_config.api_secret.get_secret_value.return_value = "test_secret"
            mock_config.timeout = 30
            mock_config.max_retries = 3
            mock_config.output_format = "json"

            mock_instance.load.return_value = mock_config
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "API Key" in result.output

    def test_config_show_no_credentials(self):
        """Test config show command without credentials."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            with patch("domaintools_client.cli.commands.config.ConfigManager") as mock_manager:
                mock_instance = Mock()
                mock_instance.is_configured.return_value = False
                mock_manager.return_value = mock_instance

                result = runner.invoke(cli, ["config", "show"])

                assert result.exit_code == 0
                assert "not configured" in result.output.lower()

    def test_config_clear(self):
        """Test config clear command."""
        runner = CliRunner()

        with patch("domaintools_client.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "clear"], input="y\n")

            assert result.exit_code == 0
            mock_instance.clear.assert_called_once()

    def test_config_test_success(self):
        """Test config test command with valid credentials."""
        runner = CliRunner()

        with patch("domaintools_client.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_client = Mock()

            # Mock successful API call
            mock_client.domain_profile.return_value = {"response": {"domain": "example.com"}}
            mock_instance.get_client.return_value = mock_client
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "test"])

            assert result.exit_code == 0
            assert "successful" in result.output.lower() or "✓" in result.output

    def test_config_test_failure(self):
        """Test config test command with invalid credentials."""
        runner = CliRunner()

        with patch("domaintools_client.cli.commands.config.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_client = Mock()

            # Mock failed API call
            from domaintools_client.api.exceptions import AuthenticationError

            mock_client.domain_profile.side_effect = AuthenticationError("Invalid credentials")
            mock_instance.get_client.return_value = mock_client
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "test"])

            assert result.exit_code == 1
            assert "failed" in result.output.lower() or "Invalid credentials" in result.output

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
    )
    def test_domain_profile_success(self):
        """Test domain profile command with mocked API."""
        runner = CliRunner()

        with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client_class:
            mock_client = Mock()
            mock_client.domain_profile.return_value = {
                "response": {"domain": "example.com", "registrant": "Example Corp"}
            }
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["domain", "profile", "example.com"])

            assert result.exit_code == 0
            assert "example.com" in result.output

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
    )
    def test_domain_profile_error(self):
        """Test domain profile command with API error."""
        runner = CliRunner()

        with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client_class:
            mock_client = Mock()
            from domaintools_client.api.exceptions import DomainToolsError

            mock_client.domain_profile.side_effect = DomainToolsError("API Error")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["domain", "profile", "nonexistent.com"])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_domain_profile_no_credentials(self):
        """Test domain profile command without credentials."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ["domain", "profile", "example.com"])

            assert result.exit_code == 1
            assert "not configured" in result.output

    @patch.dict(
        os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
    )
    def test_batch_processing(self):
        """Test batch processing functionality."""
        runner = CliRunner()

        with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client_class:
            mock_client = Mock()

            # Mock the async batch method
            async def mock_batch(domains):
                return [{"response": {"domain": domain}} for domain in domains]

            mock_client.batch_domain_profiles = mock_batch
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["batch", "example.com", "test.com"])

            assert result.exit_code == 0
            assert "example.com" in result.output
            assert "test.com" in result.output

    def test_output_format_json(self):
        """Test JSON output format."""
        runner = CliRunner()

        with patch.dict(
            os.environ, {"DOMAINTOOLS_API_KEY": "test_key", "DOMAINTOOLS_API_SECRET": "test_secret"}
        ):
            with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client_class:
                mock_client = Mock()
                mock_client.domain_profile.return_value = {"response": {"domain": "example.com"}}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    cli, ["--output", "json", "domain", "profile", "example.com"]
                )

                assert result.exit_code == 0
                # Should contain JSON-formatted output
                assert "{" in result.output and "}" in result.output

    def test_custom_config_dir(self, tmp_path):
        """Test using custom configuration directory."""
        runner = CliRunner()
        config_dir = tmp_path / "custom_config"

        # Create config file
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text('{"api_key": "test_key", "api_secret": "test_secret"}')

        with patch("domaintools_client.config.manager.DomainToolsClient") as mock_client_class:
            mock_client = Mock()
            mock_client.domain_profile.return_value = {"response": {"domain": "example.com"}}
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                cli, ["--config-dir", str(config_dir), "domain", "profile", "example.com"]
            )

            assert result.exit_code == 0
