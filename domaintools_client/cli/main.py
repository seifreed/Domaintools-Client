"""Main CLI entry point for DomainTools client."""

import sys
from pathlib import Path

import click
from rich.console import Console

from ..api.client import DomainToolsClient
from ..api.exceptions import AuthenticationError
from ..config.manager import ConfigManager
from ..formatters.output import OutputFormatter
from .commands import config_cmd, domain, iris, monitor, reputation, reverse, search, whois

console = Console()
formatter = OutputFormatter(console)


@click.group()
@click.option("--api-key", envvar="DOMAINTOOLS_API_KEY", help="DomainTools API key")
@click.option("--api-secret", envvar="DOMAINTOOLS_API_SECRET", help="DomainTools API secret")
@click.option("--config-dir", type=click.Path(), help="Configuration directory")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "tree"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(ctx, api_key, api_secret, config_dir, output):
    """Domaintools CLI - A powerful command-line interface for DomainTools API.

    This tool provides access to all DomainTools API endpoints with rich formatting
    and can also be used as a Python library.

    Configuration priority:
    1. Command-line options
    2. Environment variables
    3. Configuration file (~/.domaintools/config.json)

    Examples:
        domaintools config set --api-key YOUR_KEY --api-secret YOUR_SECRET
        domaintools domain profile example.com
        domaintools search domain "test"
        domaintools iris investigate suspicious-domain.com
    """
    ctx.ensure_object(dict)

    # Initialize config manager
    config_path = Path(config_dir) if config_dir else None
    config_mgr = ConfigManager(config_path)

    # Try to load configuration
    try:
        if api_key and api_secret:
            # Use provided credentials
            client = DomainToolsClient(api_key, api_secret)
        elif config_mgr.is_configured():
            # Use saved configuration
            client = config_mgr.get_client()
        else:
            client = None
    except (AuthenticationError, ValueError) as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        client = None

    ctx.obj["client"] = client
    ctx.obj["config_mgr"] = config_mgr
    ctx.obj["output_format"] = output
    ctx.obj["formatter"] = formatter
    ctx.obj["console"] = console


# Add command groups
cli.add_command(domain.domain)
cli.add_command(search.search)
cli.add_command(iris.iris)
cli.add_command(whois.whois)
cli.add_command(reverse.reverse)
cli.add_command(monitor.monitor)
cli.add_command(reputation.reputation)
cli.add_command(config_cmd.config)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from .. import __version__

    console = ctx.obj["console"]
    console.print(f"DomainTools CLI version: {__version__}")


@cli.command()
@click.argument("domains", nargs=-1, required=True)
@click.option("--concurrent", "-c", default=5, help="Number of concurrent requests")
@click.pass_context
def batch(ctx, domains, concurrent):
    """Process multiple domains in batch.

    Example:
        domaintools batch example.com google.com facebook.com
    """
    client = ctx.obj["client"]
    formatter = ctx.obj["formatter"]
    console = ctx.obj["console"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    import asyncio

    async def process_batch():
        """Process domain profiles in batch asynchronously."""
        results = await client.batch_domain_profiles(list(domains))
        return results

    with console.status(f"Processing {len(domains)} domains..."):
        try:
            results = asyncio.run(process_batch())

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    console.print(f"[red]Error processing {domains[i]}: {result}[/red]")
                else:
                    console.print(f"\n[bold]Results for {domains[i]}:[/bold]")
                    formatter.format_domain_profile(result)
        except Exception as e:
            console.print(f"[red]Batch processing error: {e}[/red]")
            sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
