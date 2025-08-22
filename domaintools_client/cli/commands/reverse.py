"""Reverse lookup CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def reverse(ctx):
    """Reverse lookup commands."""
    pass


@reverse.command()
@click.argument("ip")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def ip(ctx, ip, limit, raw):
    """Find domains hosted on an IP address.

    Example:
        domaintools reverse ip 8.8.8.8 --limit 50
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
        with console.status(f"Finding domains on IP {ip}..."):
            result = client.reverse_ip(ip, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, f"Reverse IP: {ip}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Reverse IP: {ip}")
        else:
            console.print(f"\n[bold cyan]Domains on IP: {ip}[/bold cyan]\n")

            if "domain_names" in result:
                domains = result["domain_names"]

                if domains:
                    console.print(f"[dim]Found {len(domains)} domains[/dim]\n")

                    # Display domains in columns for better readability
                    from rich.columns import Columns

                    displayed_domains = domains[:limit]
                    columns = Columns(displayed_domains, equal=True, expand=False)
                    console.print(columns)

                    if len(domains) > limit:
                        console.print(
                            f"\n[dim]Showing {limit} of {len(domains)} total domains[/dim]"
                        )
                else:
                    console.print("[yellow]No domains found on this IP[/yellow]")

            # Additional IP information if available
            if "ip_addresses" in result:
                ip_info = result["ip_addresses"].get(ip, {})
                if ip_info:
                    console.print("\n[bold]IP Information:[/bold]")
                    console.print(f"  Country: {ip_info.get('country', 'N/A')}")
                    console.print(f"  Organization: {ip_info.get('organization', 'N/A')}")
                    console.print(f"  ISP: {ip_info.get('isp', 'N/A')}")
    except Exception as e:
        console.print(f"[red]Error in reverse IP lookup: {e}[/red]")
        sys.exit(1)


@reverse.command()
@click.argument("query")
@click.option(
    "--mode", type=click.Choice(["current", "historic"]), default="current", help="Search mode"
)
@click.option(
    "--scope", type=click.Choice(["domain", "email", "name"]), default="domain", help="Search scope"
)
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def whois(ctx, query, mode, scope, limit, raw):
    """Search domains by WHOIS record fields.

    Find domains registered with specific email addresses, names,
    or organizations in WHOIS records.

    Example:
        domaintools reverse whois "john.doe@example.com" --mode historic
        domaintools reverse whois "Example Corp" --scope name
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
        kwargs = {"mode": mode, "scope": scope, "limit": limit}

        with console.status(f"Searching reverse WHOIS for '{query}'..."):
            result = client.reverse_whois(query, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, "Reverse WHOIS Results")
        elif output_format == "tree":
            formatter.format_tree(result, "Reverse WHOIS Results")
        else:
            console.print(f"\n[bold cyan]Reverse WHOIS Search: '{query}'[/bold cyan]")
            console.print(f"[dim]Mode: {mode}, Scope: {scope}[/dim]\n")

            if "results" in result:
                domains = result["results"]

                if domains:
                    from rich.table import Table

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Domain", style="cyan")
                    table.add_column("Created", style="yellow")
                    table.add_column("Registrar", style="green")

                    if mode == "historic":
                        table.add_column("Last Seen", style="blue")

                    for domain_info in domains[:limit]:
                        row = [
                            domain_info.get("domain", "N/A"),
                            str(domain_info.get("created", "N/A")),
                            domain_info.get("registrar", "N/A")[:30],
                        ]

                        if mode == "historic":
                            row.append(str(domain_info.get("last_seen", "N/A")))

                        table.add_row(*row)

                    console.print(table)

                    total = result.get("total_results", len(domains))
                    if total > limit:
                        console.print(f"\n[dim]Showing {limit} of {total} total results[/dim]")
                else:
                    console.print("[yellow]No domains found matching the search criteria[/yellow]")
            else:
                console.print("[yellow]No results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in reverse WHOIS search: {e}[/red]")
        sys.exit(1)


@reverse.command()
@click.argument("nameserver")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def nameserver(ctx, nameserver, limit, raw):
    """Find domains using a specific nameserver.

    Example:
        domaintools reverse nameserver ns1.example.com
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
        with console.status(f"Finding domains using nameserver {nameserver}..."):
            # Using name_server_monitor as reverse nameserver lookup
            result = client.name_server_monitor(nameserver, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, f"Reverse Nameserver: {nameserver}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Reverse Nameserver: {nameserver}")
        else:
            console.print(f"\n[bold cyan]Domains using nameserver: {nameserver}[/bold cyan]\n")

            if "domains" in result:
                domains = result["domains"]

                if domains:
                    console.print(f"[dim]Found {len(domains)} domains[/dim]\n")

                    from rich.table import Table

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Domain", style="cyan")
                    table.add_column("First Seen", style="yellow")
                    table.add_column("Last Seen", style="green")

                    for domain_info in domains[:limit]:
                        table.add_row(
                            domain_info.get("domain", "N/A"),
                            str(domain_info.get("first_seen", "N/A")),
                            str(domain_info.get("last_seen", "N/A")),
                        )

                    console.print(table)

                    if len(domains) > limit:
                        console.print(
                            f"\n[dim]Showing {limit} of {len(domains)} total domains[/dim]"
                        )
                else:
                    console.print("[yellow]No domains found using this nameserver[/yellow]")
            else:
                console.print("[yellow]No results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in reverse nameserver lookup: {e}[/red]")
        sys.exit(1)
