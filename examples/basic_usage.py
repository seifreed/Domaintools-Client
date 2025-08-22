#!/usr/bin/env python3
"""Basic usage examples for DomainTools Client library."""

import asyncio

from rich.console import Console

from domaintools_client import ConfigManager, DomainToolsClient
from domaintools_client.formatters import OutputFormatter

# Initialize console for rich output
console = Console()
formatter = OutputFormatter(console)


def example_with_credentials():
    """Example using direct credentials."""
    # Initialize client with credentials
    client = DomainToolsClient(
        api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET"  # nosec B106 - This is example code
    )

    # Get domain profile
    try:
        profile = client.domain_profile("example.com")
        formatter.format_domain_profile(profile)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def example_with_config():
    """Example using configuration manager."""
    # Use configuration manager
    config_mgr = ConfigManager()

    if not config_mgr.is_configured():
        console.print("[yellow]Please configure your API credentials first[/yellow]")
        console.print("Run: domaintools config set")
        return

    # Get configured client
    client = config_mgr.get_client()

    # Perform searches
    try:
        # Domain search
        results = client.domain_search("test", max_results=5)
        formatter.format_search_results(results, "Domain Search")

        # Reputation check
        reputation = client.reputation("suspicious-site.com")
        formatter.format_reputation(reputation)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def example_async_operations():
    """Example of async operations."""
    config_mgr = ConfigManager()

    if not config_mgr.is_configured():
        console.print("[yellow]Please configure your API credentials first[/yellow]")
        return

    client = config_mgr.get_client()

    # Check multiple domains concurrently
    domains = ["example.com", "google.com", "github.com"]

    console.print(f"[cyan]Checking {len(domains)} domains concurrently...[/cyan]")

    try:
        profiles = await client.batch_domain_profiles(domains)

        for i, profile in enumerate(profiles):
            if isinstance(profile, Exception):
                console.print(f"[red]Error for {domains[i]}: {profile}[/red]")
            else:
                console.print(
                    f"[green]✓[/green] {domains[i]}: {profile.get('registration', {}).get('registrar', 'N/A')}"
                )

    except Exception as e:
        console.print(f"[red]Error in batch processing: {e}[/red]")


def example_error_handling():
    """Example of proper error handling."""
    from domaintools_client.api.exceptions import (
        AuthenticationError,
        DomainToolsError,
        InvalidRequestError,
        RateLimitError,
    )

    config_mgr = ConfigManager()

    if not config_mgr.is_configured():
        console.print("[yellow]Please configure your API credentials first[/yellow]")
        return

    client = config_mgr.get_client()

    try:
        # Try to get profile for an invalid domain
        profile = client.domain_profile("this-is-not-a-valid-domain-12345.xyz")
        formatter.format_domain_profile(profile)

    except AuthenticationError:
        console.print("[red]Authentication failed. Please check your API credentials.[/red]")
    except RateLimitError:
        console.print(
            "[yellow]Rate limit exceeded. Please wait before making more requests.[/yellow]"
        )
    except InvalidRequestError as e:
        console.print(f"[orange]Invalid request: {e}[/orange]")
    except DomainToolsError as e:
        console.print(f"[red]DomainTools API error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


def example_iris_investigation():
    """Example of Iris investigation."""
    config_mgr = ConfigManager()

    if not config_mgr.is_configured():
        console.print("[yellow]Please configure your API credentials first[/yellow]")
        return

    client = config_mgr.get_client()

    try:
        # Investigate a domain
        console.print("[cyan]Investigating domain with Iris...[/cyan]")
        result = client.iris_investigate("example.com", include_whois=True)

        # Display risk score
        if "risk_score" in result:
            score = result["risk_score"]
            color = "green" if score < 30 else "yellow" if score < 70 else "red"
            console.print(f"Risk Score: [{color}]{score}[/{color}]")

        # Display threat indicators
        if "threat_indicators" in result:
            console.print("\n[bold]Threat Indicators:[/bold]")
            for indicator in result["threat_indicators"]:
                console.print(f"  ⚠ {indicator}")

    except Exception as e:
        console.print(f"[red]Error in Iris investigation: {e}[/red]")


def main():
    """Run examples."""
    console.print("[bold cyan]DomainTools Client - Usage Examples[/bold cyan]\n")

    # Choose which example to run
    console.print("1. Example with configuration")
    console.print("2. Async operations example")
    console.print("3. Error handling example")
    console.print("4. Iris investigation example")

    choice = input("\nSelect an example (1-4): ")

    if choice == "1":
        example_with_config()
    elif choice == "2":
        asyncio.run(example_async_operations())
    elif choice == "3":
        example_error_handling()
    elif choice == "4":
        example_iris_investigation()
    else:
        console.print("[yellow]Invalid choice[/yellow]")


if __name__ == "__main__":
    main()
