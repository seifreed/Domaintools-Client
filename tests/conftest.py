"""Test configuration and fixtures."""

from unittest.mock import MagicMock, Mock

import pytest

from domaintools_client.api.client import DomainToolsClient
from domaintools_client.config.manager import DomainToolsConfig


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    mock = Mock(spec=DomainToolsClient)
    mock.domain_profile.return_value = {
        "response": {
            "domain": "example.com",
            "registrant": "Example Corp",
            "registration": {"created": "2000-01-01"},
        }
    }
    mock.whois.return_value = {"record": "example.com domain info..."}
    return mock


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = DomainToolsConfig(
        api_key="test_key_123",
        api_secret="test_secret_456",
        timeout=30,
        max_retries=3,
        output_format="json",
    )
    return config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_domaintools_api():
    """Mock the DomainTools API responses."""
    mock = MagicMock()

    # Mock successful responses
    mock.domain_profile.return_value.data.return_value = {"response": {"domain": "example.com"}}
    mock.whois.return_value.data.return_value = {"record": "example.com whois data"}
    mock.domain_search.return_value.data.return_value = {"results": [{"domain": "example.com"}]}

    return mock
