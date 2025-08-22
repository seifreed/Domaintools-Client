"""Tests for the DomainTools API client."""

from unittest.mock import Mock, patch

import pytest
from domaintools.exceptions import BadRequestException, NotAuthorizedException, ServiceException

from domaintools_client.api.client import DomainToolsClient
from domaintools_client.api.exceptions import (
    AuthenticationError,
    DomainToolsError,
    InvalidRequestError,
    RateLimitError,
)


class TestDomainToolsClient:
    """Test the DomainTools API client."""

    def test_init_success(self):
        """Test successful client initialization."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            client = DomainToolsClient("test_key", "test_secret")
            assert client.api_key == "test_key"
            assert client.api_secret == "test_secret"
            mock_api.assert_called_once_with("test_key", "test_secret", api_url=None)

    def test_init_with_custom_url(self):
        """Test client initialization with custom URL."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            client = DomainToolsClient("key", "secret", "https://custom.api.url")
            assert client.api_url == "https://custom.api.url"
            mock_api.assert_called_once_with("key", "secret", api_url="https://custom.api.url")

    def test_init_failure(self):
        """Test client initialization failure."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_api.side_effect = Exception("Connection failed")

            with pytest.raises(AuthenticationError) as exc_info:
                DomainToolsClient("bad_key", "bad_secret")

            assert "Failed to initialize API client" in str(exc_info.value)

    def test_handle_authentication_error(self):
        """Test handling of authentication errors."""
        with patch("domaintools_client.api.client.DomainToolsAPI"):
            client = DomainToolsClient("key", "secret")

            with pytest.raises(AuthenticationError):
                client._handle_exception(NotAuthorizedException("Invalid credentials"))

    def test_handle_bad_request_error(self):
        """Test handling of bad request errors."""
        with patch("domaintools_client.api.client.DomainToolsAPI"):
            client = DomainToolsClient("key", "secret")

            with pytest.raises(InvalidRequestError):
                client._handle_exception(BadRequestException("Bad request"))

    def test_handle_rate_limit_error(self):
        """Test handling of rate limit errors."""
        with patch("domaintools_client.api.client.DomainToolsAPI"):
            client = DomainToolsClient("key", "secret")

            with pytest.raises(RateLimitError):
                client._handle_exception(ServiceException("Rate limit exceeded"))

    def test_handle_generic_service_error(self):
        """Test handling of generic service errors."""
        with patch("domaintools_client.api.client.DomainToolsAPI"):
            client = DomainToolsClient("key", "secret")

            with pytest.raises(DomainToolsError):
                client._handle_exception(ServiceException("Service unavailable"))

    def test_handle_unexpected_error(self):
        """Test handling of unexpected errors."""
        with patch("domaintools_client.api.client.DomainToolsAPI"):
            client = DomainToolsClient("key", "secret")

            with pytest.raises(DomainToolsError) as exc_info:
                client._handle_exception(ValueError("Unexpected"))

            assert "Unexpected error" in str(exc_info.value)

    def test_domain_profile_success(self):
        """Test successful domain profile request."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"domain": "example.com"}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            result = client.domain_profile("example.com")

            assert result == {"domain": "example.com"}
            mock_api.return_value.domain_profile.assert_called_once_with("example.com")

    def test_domain_profile_error(self):
        """Test domain profile request with error."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_api.return_value.domain_profile.side_effect = ServiceException("API Error")

            client = DomainToolsClient("key", "secret")

            with pytest.raises(DomainToolsError):
                client.domain_profile("example.com")

    def test_domain_search(self):
        """Test domain search functionality."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"results": ["example.com"]}
            mock_api.return_value.domain_search.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            result = client.domain_search("example", max_results=100)

            assert result == {"results": ["example.com"]}
            mock_api.return_value.domain_search.assert_called_once_with("example", max_results=100)

    def test_whois(self):
        """Test WHOIS functionality."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"record": "whois data"}
            mock_api.return_value.whois.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            result = client.whois("example.com")

            assert result == {"record": "whois data"}
            mock_api.return_value.whois.assert_called_once_with("example.com")

    def test_iris_investigate(self):
        """Test Iris investigate functionality."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"risk_score": 80}
            mock_api.return_value.iris_investigate.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            result = client.iris_investigate("suspicious.com")

            assert result == {"risk_score": 80}
            mock_api.return_value.iris_investigate.assert_called_once_with("suspicious.com")

    @pytest.mark.asyncio
    async def test_async_domain_profile(self):
        """Test async domain profile functionality."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"domain": "example.com"}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            result = await client.async_domain_profile("example.com")

            assert result == {"domain": "example.com"}

    @pytest.mark.asyncio
    async def test_batch_domain_profiles(self):
        """Test batch domain profiles functionality."""
        with patch("domaintools_client.api.client.DomainToolsAPI") as mock_api:
            mock_response = Mock()
            mock_response.data.return_value = {"domain": "example.com"}
            mock_api.return_value.domain_profile.return_value = mock_response

            client = DomainToolsClient("key", "secret")
            domains = ["example.com", "test.com"]
            results = await client.batch_domain_profiles(domains)

            assert len(results) == 2
            assert all("domain" in result or isinstance(result, Exception) for result in results)
