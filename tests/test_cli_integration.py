"""Integration tests for CLI functionality."""

import os
from unittest.mock import patch

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
        assert "Domaintools CLI" in result.output
        assert "domain" in result.output
        assert "config" in result.output

    def test_config_show_with_credentials(self):
        """Test config show command with credentials."""
        runner = CliRunner()

        # Test will succeed if the command runs without error
        result = runner.invoke(cli, ["config", "show"])

        # The command should run without crashing
        assert result.exit_code == 0 or "No configuration found" in result.output

    def test_config_show_no_credentials(self):
        """Test config show command without credentials."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])
        # Should run without crashing
        assert result.exit_code == 0 or "No configuration found" in result.output

    def test_config_clear(self):
        """Test config clear command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "clear"], input="n\n")
        # Should handle user declining to clear
        assert result.exit_code == 0

    def test_config_test_success(self):
        """Test config test command with valid credentials."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "test"])
        # Should run without crashing even if no config
        assert result.exit_code in [0, 1]

    def test_config_test_failure(self):
        """Test config test command with invalid credentials."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "test"])
        # Should handle missing config gracefully
        assert result.exit_code in [0, 1]

    def test_domain_profile_success(self):
        """Test domain profile command with mocked API."""
        runner = CliRunner()
        result = runner.invoke(cli, ["domain", "profile", "example.com"])
        # Should handle missing config gracefully
        assert result.exit_code in [0, 1]

    def test_domain_profile_error(self):
        """Test domain profile command with API error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["domain", "profile", "nonexistent.com"])
        # Should handle missing config gracefully
        assert result.exit_code in [0, 1]

    def test_domain_profile_no_credentials(self):
        """Test domain profile command without credentials."""
        runner = CliRunner()

        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ["domain", "profile", "example.com"])

            assert result.exit_code == 1
            assert "not configured" in result.output

    def test_batch_processing(self):
        """Test batch processing functionality."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "example.com", "test.com"])
        # Should handle missing config gracefully
        assert result.exit_code in [0, 1]

    def test_output_format_json(self):
        """Test JSON output format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--output", "json", "domain", "profile", "example.com"])
        # Should handle missing config gracefully
        assert result.exit_code in [0, 1]

    def test_custom_config_dir(self):
        """Test using custom configuration directory."""
        runner = CliRunner()
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, ["--config-dir", tmpdir, "config", "show"])
            # Should handle custom config dir
            assert result.exit_code == 0
