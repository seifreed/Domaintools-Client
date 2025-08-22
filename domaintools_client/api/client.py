"""Core DomainTools API client."""

import asyncio
from typing import Any, Dict, List, NoReturn, Optional, Union

from domaintools import API as DomainToolsAPI
from domaintools.exceptions import BadRequestException, NotAuthorizedException, ServiceException

from .exceptions import AuthenticationError, DomainToolsError, InvalidRequestError, RateLimitError


class DomainToolsClient:
    """Enhanced DomainTools API client with additional features."""

    def __init__(self, api_key: str, api_secret: str, api_url: Optional[str] = None):
        """Initialize the DomainTools client.

        Args:
            api_key: DomainTools API key
            api_secret: DomainTools API secret
            api_url: Optional custom API URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url

        try:
            self.api = DomainToolsAPI(api_key, api_secret, api_url=api_url)
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize API client: {str(e)}") from e

    def _handle_exception(self, e: Exception) -> NoReturn:
        """Convert DomainTools exceptions to custom exceptions."""
        if isinstance(e, NotAuthorizedException):
            raise AuthenticationError(str(e))
        elif isinstance(e, BadRequestException):
            raise InvalidRequestError(str(e))
        elif isinstance(e, ServiceException):
            if "rate limit" in str(e).lower():
                raise RateLimitError(str(e))
            raise DomainToolsError(str(e))
        else:
            raise DomainToolsError(f"Unexpected error: {str(e)}")

    def domain_profile(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive domain profile information.

        Args:
            domain: Domain name to query

        Returns:
            Domain profile data
        """
        try:
            response = self.api.domain_profile(domain)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def domain_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search for domains based on various criteria.

        Args:
            query: Search query
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        try:
            response = self.api.domain_search(query, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def iris_investigate(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Iris Investigate API for domain investigation.

        Args:
            domain: Domain to investigate
            **kwargs: Additional parameters

        Returns:
            Investigation results
        """
        try:
            response = self.api.iris_investigate(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def iris_enrich(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Iris Enrich API for domain enrichment.

        Args:
            domain: Domain to enrich
            **kwargs: Additional parameters

        Returns:
            Enrichment data
        """
        try:
            response = self.api.iris_enrich(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def iris_detect(self, **kwargs) -> Dict[str, Any]:
        """Iris Detect API for threat detection.

        Args:
            **kwargs: Detection parameters

        Returns:
            Detection results
        """
        try:
            response = self.api.iris_detect(**kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def whois(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Get WHOIS information for a domain.

        Args:
            domain: Domain name
            **kwargs: Additional parameters

        Returns:
            WHOIS data
        """
        try:
            response = self.api.whois(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def whois_history(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Get historical WHOIS information for a domain.

        Args:
            domain: Domain name
            **kwargs: Additional parameters

        Returns:
            Historical WHOIS data
        """
        try:
            response = self.api.whois_history(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def reverse_ip(self, ip: str, **kwargs) -> Dict[str, Any]:
        """Get domains hosted on an IP address.

        Args:
            ip: IP address
            **kwargs: Additional parameters

        Returns:
            Reverse IP lookup results
        """
        try:
            response = self.api.reverse_ip(ip, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def reverse_whois(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search domains by WHOIS record fields.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            Reverse WHOIS results
        """
        try:
            response = self.api.reverse_whois(query, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def host_domains(self, ip: str, **kwargs) -> Dict[str, Any]:
        """Get all domains hosted on an IP address.

        Args:
            ip: IP address
            **kwargs: Additional parameters

        Returns:
            Host domains data
        """
        try:
            response = self.api.host_domains(ip, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def name_server_monitor(self, nameserver: str, **kwargs) -> Dict[str, Any]:
        """Monitor domains using a specific nameserver.

        Args:
            nameserver: Nameserver to monitor
            **kwargs: Additional parameters

        Returns:
            Nameserver monitor data
        """
        try:
            response = self.api.name_server_monitor(nameserver, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def registrant_monitor(self, query: str, **kwargs) -> Dict[str, Any]:
        """Monitor domains by registrant.

        Args:
            query: Registrant query
            **kwargs: Additional parameters

        Returns:
            Registrant monitor data
        """
        try:
            response = self.api.registrant_monitor(query, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def reputation(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Get domain reputation score.

        Args:
            domain: Domain name
            **kwargs: Additional parameters

        Returns:
            Reputation data
        """
        try:
            response = self.api.reputation(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def parsed_whois(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Get parsed WHOIS data.

        Args:
            domain: Domain name
            **kwargs: Additional parameters

        Returns:
            Parsed WHOIS data
        """
        try:
            response = self.api.parsed_whois(domain, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    def brand_monitor(self, query: str, **kwargs) -> Dict[str, Any]:
        """Monitor domains for brand protection.

        Args:
            query: Brand query
            **kwargs: Additional parameters

        Returns:
            Brand monitor data
        """
        try:
            response = self.api.brand_monitor(query, **kwargs)
            return response.data()
        except Exception as e:
            self._handle_exception(e)

    async def async_domain_profile(self, domain: str) -> Dict[str, Any]:
        """Async version of domain_profile."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.domain_profile, domain)

    async def async_domain_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Async version of domain_search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.domain_search(query, **kwargs))

    async def batch_domain_profiles(
        self, domains: List[str]
    ) -> List[Union[Dict[str, Any], BaseException]]:
        """Get profiles for multiple domains concurrently.

        Args:
            domains: List of domain names

        Returns:
            List of domain profiles
        """
        tasks = [self.async_domain_profile(domain) for domain in domains]
        return await asyncio.gather(*tasks, return_exceptions=True)
