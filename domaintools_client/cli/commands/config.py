"""Configuration management commands."""

import sys

import click
from pydantic import SecretStr
from rich.prompt import Confirm, Prompt


@click.group()
@click.pass_context
def config(ctx):
    """Manage DomainTools API configuration."""
    pass


@config.command()
@click.option("--api-key", help="DomainTools API key")
@click.option("--api-secret", help="DomainTools API secret")
@click.option("--api-url", help="Custom API URL")
@click.option("--timeout", type=int, help="Request timeout in seconds")
@click.option("--max-retries", type=int, help="Maximum number of retries")
@click.option(
    "--output-format", type=click.Choice(["json", "table", "tree"]), help="Default output format"
)
@click.pass_context
def set(ctx, api_key, api_secret, api_url, timeout, max_retries, output_format):
    """Set configuration values.

    If no options are provided, will prompt interactively.
    """
    config_mgr = ctx.obj["config_mgr"]
    console = ctx.obj["console"]

    # Interactive mode if no options provided
    if not any([api_key, api_secret, api_url, timeout, max_retries, output_format]):
        console.print("[cyan]DomainTools Configuration Setup[/cyan]")
        console.print("Enter your API credentials (press Enter to skip)")

        api_key = Prompt.ask("API Key", default="", show_default=False)
        api_secret = Prompt.ask("API Secret", password=True, default="", show_default=False)
        api_url = Prompt.ask("API URL (optional)", default="", show_default=False) or None
        timeout = Prompt.ask("Timeout (seconds)", default="30")
        max_retries = Prompt.ask("Max Retries", default="3")
        output_format = Prompt.ask(
            "Output Format", choices=["json", "table", "tree"], default="table"
        )

    # Build config update dict
    updates = {}
    if api_key:
        updates["api_key"] = api_key
    if api_secret:
        updates["api_secret"] = SecretStr(api_secret)
    if api_url:
        updates["api_url"] = api_url
    if timeout:
        updates["timeout"] = int(timeout)
    if max_retries:
        updates["max_retries"] = int(max_retries)
    if output_format:
        updates["output_format"] = output_format

    if not updates:
        console.print("[yellow]No configuration changes made[/yellow]")
        return

    try:
        # Update and save configuration
        config = config_mgr.update(**updates)
        config_mgr.save(config)
        console.print("[green]Configuration saved successfully![/green]")

        # Test the configuration
        if api_key or api_secret:
            if Confirm.ask("Test API connection?", default=True):
                try:
                    client = config_mgr.get_client()
                    # Try a simple API call
                    client.domain_profile("example.com")
                    console.print("[green]API connection successful![/green]")
                except Exception as e:
                    console.print(f"[red]API connection failed: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")
        sys.exit(1)


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration (secrets are hidden)."""
    config_mgr = ctx.obj["config_mgr"]
    console = ctx.obj["console"]

    try:
        config = config_mgr.load()

        from rich.table import Table

        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("API Key", config.api_key[:10] + "..." if config.api_key else "Not set")
        table.add_row("API Secret", "****" if config.api_secret else "Not set")
        table.add_row("API URL", config.api_url or "Default")
        table.add_row("Timeout", str(config.timeout))
        table.add_row("Max Retries", str(config.max_retries))
        table.add_row("Output Format", config.output_format)
        table.add_row("Config File", str(config_mgr.config_file))

        console.print(table)
    except Exception as e:
        console.print(f"[red]No configuration found: {e}[/red]")
        console.print("Run 'domaintools config set' to create configuration")


@config.command()
@click.pass_context
def clear(ctx):
    """Clear saved configuration."""
    config_mgr = ctx.obj["config_mgr"]
    console = ctx.obj["console"]

    if Confirm.ask("Are you sure you want to clear all configuration?", default=False):
        config_mgr.clear()
        console.print("[green]Configuration cleared[/green]")
    else:
        console.print("[yellow]Configuration not changed[/yellow]")


@config.command()
@click.pass_context
def test(ctx):
    """Test API configuration."""
    config_mgr = ctx.obj["config_mgr"]
    console = ctx.obj["console"]

    try:
        client = config_mgr.get_client()

        with console.status("Testing API connection..."):
            # Try a simple API call
            client.domain_profile("example.com")

        console.print("[green]✓ API connection successful![/green]")
        console.print("[dim]Successfully retrieved profile for example.com[/dim]")
    except Exception as e:
        console.print(f"[red]✗ API connection failed: {e}[/red]")
        console.print("\n[yellow]Please check your API credentials and try again[/yellow]")
        console.print("Run 'domaintools config set' to update credentials")
        sys.exit(1)
