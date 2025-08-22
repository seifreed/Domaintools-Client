"""Search-related CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def search(ctx):
    """Search commands for domains and related data."""
    pass


@search.command()
@click.argument("query")
@click.option("--max-results", "-m", type=int, default=100, help="Maximum number of results")
@click.option("--active-only", is_flag=True, help="Show only active domains")
@click.option("--deleted-only", is_flag=True, help="Show only deleted domains")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def domain(ctx, query, max_results, active_only, deleted_only, raw):
    """Search for domains based on various criteria.

    Example:
        domaintools search domain "example" --max-results 50
    """
    client = ctx.obj["client"]
    formatter = ctx.obj["formatter"]
    console = ctx.obj["console"]
    output_format = ctx.obj["output_format"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    try:
        kwargs = {"max_results": max_results}
        if active_only:
            kwargs["active"] = True
        if deleted_only:
            kwargs["deleted"] = True

        with console.status(f"Searching domains for '{query}'..."):
            result = client.domain_search(query, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, "Domain Search Results")
        elif output_format == "tree":
            formatter.format_tree(result, "Domain Search Results")
        else:
            formatter.format_search_results(result, "Domain")
    except Exception as e:
        console.print(f"[red]Error searching domains: {e}[/red]")
        sys.exit(1)


@search.command()
@click.argument("query")
@click.option(
    "--mode", type=click.Choice(["current", "historic"]), default="current", help="Search mode"
)
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def reverse_whois(ctx, query, mode, limit, raw):
    """Search domains by WHOIS record fields.

    Search for domains by registrant name, email, or other WHOIS fields.

    Example:
        domaintools search reverse-whois "john.doe@example.com" --mode historic
    """
    client = ctx.obj["client"]
    formatter = ctx.obj["formatter"]
    console = ctx.obj["console"]
    output_format = ctx.obj["output_format"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    try:
        with console.status(f"Searching reverse WHOIS for '{query}'..."):
            result = client.reverse_whois(query, mode=mode, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, "Reverse WHOIS Results")
        elif output_format == "tree":
            formatter.format_tree(result, "Reverse WHOIS Results")
        else:
            # Format reverse WHOIS results
            if "results" in result:
                from rich.table import Table

                table = Table(title=f"Reverse WHOIS Results for '{query}'")
                table.add_column("Domain", style="cyan")
                table.add_column("Created", style="yellow")
                table.add_column("Updated", style="green")

                for domain_info in result["results"][:limit]:
                    table.add_row(
                        domain_info.get("domain", "N/A"),
                        str(domain_info.get("created", "N/A")),
                        str(domain_info.get("updated", "N/A")),
                    )

                console.print(table)

                total = result.get("total_results", len(result["results"]))
                if total > limit:
                    console.print(f"\n[dim]Showing {limit} of {total} total results[/dim]")
            else:
                console.print("[yellow]No results found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in reverse WHOIS search: {e}[/red]")
        sys.exit(1)


@search.command()
@click.argument("ip")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def reverse_ip(ctx, ip, limit, raw):
    """Find domains hosted on an IP address.

    Example:
        domaintools search reverse-ip 192.168.1.1
    """
    client = ctx.obj["client"]
    formatter = ctx.obj["formatter"]
    console = ctx.obj["console"]
    output_format = ctx.obj["output_format"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    try:
        with console.status(f"Searching domains on IP {ip}..."):
            result = client.reverse_ip(ip, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, f"Reverse IP: {ip}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Reverse IP: {ip}")
        else:
            # Format reverse IP results
            if "domain_names" in result:
                domains = result["domain_names"]
                console.print(f"\n[bold cyan]Domains on IP {ip}[/bold cyan]")
                console.print(f"[dim]Total domains: {len(domains)}[/dim]\n")

                for domain in domains[:limit]:
                    console.print(f"  • {domain}")

                if len(domains) > limit:
                    console.print(f"\n[dim]... and {len(domains) - limit} more[/dim]")
            else:
                console.print("[yellow]No domains found on this IP[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in reverse IP search: {e}[/red]")
        sys.exit(1)


@search.command()
@click.argument("ip")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def host_domains(ctx, ip, limit, raw):
    """Get all domains hosted on an IP address with additional details.

    Example:
        domaintools search host-domains 192.168.1.1
    """
    client = ctx.obj["client"]
    formatter = ctx.obj["formatter"]
    console = ctx.obj["console"]
    output_format = ctx.obj["output_format"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    try:
        with console.status(f"Fetching host domains for IP {ip}..."):
            result = client.host_domains(ip, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, f"Host Domains: {ip}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Host Domains: {ip}")
        else:
            # Format host domains results
            if "domains" in result:
                from rich.table import Table

                table = Table(title=f"Domains hosted on {ip}")
                table.add_column("Domain", style="cyan")
                table.add_column("First Seen", style="yellow")
                table.add_column("Last Seen", style="green")

                for domain_info in result["domains"][:limit]:
                    table.add_row(
                        domain_info.get("domain", "N/A"),
                        str(domain_info.get("first_seen", "N/A")),
                        str(domain_info.get("last_seen", "N/A")),
                    )

                console.print(table)

                total = len(result["domains"])
                if total > limit:
                    console.print(f"\n[dim]Showing {limit} of {total} total domains[/dim]")
            else:
                console.print("[yellow]No domains found on this IP[/yellow]")
    except Exception as e:
        console.print(f"[red]Error fetching host domains: {e}[/red]")
        sys.exit(1)
