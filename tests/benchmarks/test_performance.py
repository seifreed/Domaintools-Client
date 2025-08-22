"""Performance benchmarks for the DomainTools Client."""

from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from domaintools_client.api.client import DomainToolsClient
from domaintools_client.config.manager import ConfigManager
from domaintools_client.formatters.output import OutputFormatter


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for performance testing."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"response": {"domain": "example.com"}}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("test_key", "test_secret")
            return client

    def test_client_initialization_performance(self, benchmark):
        """Benchmark client initialization time."""

        def initialize_client():
            with patch("domaintools_client.api.client.DomainToolsAPI"):
                return DomainToolsClient("test_key", "test_secret")

        result = benchmark(initialize_client)
        assert result is not None

    def test_domain_profile_performance(self, benchmark, mock_client):
        """Benchmark domain profile request performance."""

        def get_domain_profile():
            return mock_client.domain_profile("example.com")

        result = benchmark(get_domain_profile)
        assert "response" in result

    def test_config_loading_performance(self, benchmark, tmp_path):
        """Benchmark configuration loading performance."""
        # Create test config file
        config_file = tmp_path / "config.json"
        config_file.write_text('{"api_key": "test", "api_secret": "test"}')

        def load_config():
            config_mgr = ConfigManager(config_dir=tmp_path)
            return config_mgr.load()

        result = benchmark(load_config)
        assert result.api_key == "test"

    def test_formatter_performance(self, benchmark):
        """Benchmark output formatting performance."""
        console = Console()
        formatter = OutputFormatter(console)

        test_data = {
            "response": {
                "domain": "example.com",
                "registrant": "Test Corp",
                "registration": {"created": "2000-01-01", "expires": "2025-01-01"},
                "ip_addresses": [
                    {"address": {"ip": "192.0.2.1"}},
                    {"address": {"ip": "192.0.2.2"}},
                ],
                "name_servers": ["ns1.example.com", "ns2.example.com"],
            }
        }

        def format_domain_profile():
            formatter.format_domain_profile(test_data)

        benchmark(format_domain_profile)

    def test_json_formatting_performance(self, benchmark):
        """Benchmark JSON formatting performance."""
        console = Console()
        formatter = OutputFormatter(console)

        large_data = {
            "results": [{"domain": f"example{i}.com", "created": "2000-01-01"} for i in range(100)]
        }

        def format_json():
            formatter.format_json(large_data, "Test Data")

        benchmark(format_json)

    def test_batch_processing_simulation(self, benchmark):
        """Benchmark batch processing simulation."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"response": {"domain": "test.com"}}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("test_key", "test_secret")

            def batch_process_domains():
                domains = [f"test{i}.com" for i in range(10)]
                results = []
                for domain in domains:
                    result = client.domain_profile(domain)
                    results.append(result)
                return results

            results = benchmark(batch_process_domains)
            assert len(results) == 10

    def test_memory_usage_simulation(self, benchmark):
        """Test memory usage during typical operations."""

        def memory_intensive_operation():
            # Simulate processing large amounts of data
            data = []
            for i in range(1000):
                domain_data = {
                    "domain": f"example{i}.com",
                    "profile": {
                        "registrant": f"User {i}",
                        "registration": {"created": "2000-01-01", "expires": "2025-01-01"},
                        "nameservers": [f"ns{j}.example{i}.com" for j in range(4)],
                    },
                }
                data.append(domain_data)
            return len(data)

        result = benchmark(memory_intensive_operation)
        assert result == 1000

    @pytest.mark.parametrize("domain_count", [1, 5, 10, 25, 50])
    def test_scaling_performance(self, benchmark, domain_count):
        """Test performance scaling with different domain counts."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"response": {"domain": "test.com"}}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("test_key", "test_secret")

            def process_domains():
                domains = [f"test{i}.com" for i in range(domain_count)]
                results = []
                for domain in domains:
                    result = client.domain_profile(domain)
                    results.append(result)
                return results

            results = benchmark(process_domains)
            assert len(results) == domain_count

    def test_import_time_performance(self, benchmark):
        """Benchmark module import time."""

        def import_domaintools_client():
            import importlib
            import sys

            # Remove module if already imported
            modules_to_remove = [
                name for name in sys.modules.keys() if name.startswith("domaintools_client")
            ]
            for module in modules_to_remove:
                del sys.modules[module]

            # Import the main module
            return importlib.import_module("domaintools_client")

        result = benchmark(import_domaintools_client)
        assert result is not None

    def test_configuration_parsing_performance(self, benchmark):
        """Benchmark configuration file parsing."""
        import json

        import yaml

        config_data = {
            "api": {
                "key": "test_key_12345",
                "secret": "test_secret_67890",
                "url": "https://api.domaintools.com",
            },
            "settings": {"timeout": 30, "max_retries": 3, "output_format": "json"},
        }

        def parse_yaml_config():
            yaml_content = yaml.dump(config_data)
            return yaml.safe_load(yaml_content)

        def parse_json_config():
            json_content = json.dumps(config_data)
            return json.loads(json_content)

        # Benchmark both formats
        yaml_result = benchmark(parse_yaml_config)
        json_result = benchmark(parse_json_config)

        assert yaml_result == config_data
        assert json_result == config_data
