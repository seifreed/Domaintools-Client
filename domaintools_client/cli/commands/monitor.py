"""Monitoring CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def monitor(ctx):
    """Domain monitoring commands."""
    pass


@monitor.command()
@click.argument("query")
@click.option("--days-back", type=int, default=30, help="Number of days to look back")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--include-deleted", is_flag=True, help="Include deleted domains")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def brand(ctx, query, days_back, limit, include_deleted, raw):
    """Monitor domains for brand protection.

    Track new domain registrations that may be attempting to
    impersonate or infringe on your brand.

    Example:
        domaintools monitor brand "mycompany" --days-back 7
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
        kwargs = {"days_back": days_back, "limit": limit}
        if include_deleted:
            kwargs["include_deleted"] = True

        with console.status(f"Monitoring brand '{query}'..."):
            result = client.brand_monitor(query, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Brand Monitor: {query}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Brand Monitor: {query}")
        else:
            console.print(f"\n[bold cyan]Brand Monitor: '{query}'[/bold cyan]")
            console.print(f"[dim]Last {days_back} days[/dim]\n")

            if "domains" in result:
                domains = result["domains"]

                if domains:
                    from rich.table import Table

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Domain", style="cyan")
                    table.add_column("Discovered", style="yellow")
                    table.add_column("Registrar", style="green")
                    table.add_column("Risk", style="red")

                    for domain_info in domains[:limit]:
                        risk_score = domain_info.get("risk_score", 0)
                        if risk_score >= 70:
                            risk_color = "red"
                        elif risk_score >= 40:
                            risk_color = "yellow"
                        else:
                            risk_color = "green"

                        table.add_row(
                            domain_info.get("domain", "N/A"),
                            str(domain_info.get("discovered", "N/A")),
                            domain_info.get("registrar", "N/A")[:30],
                            f"[{risk_color}]{risk_score}[/{risk_color}]",
                        )

                    console.print(table)

                    # Summary statistics
                    total = len(domains)
                    high_risk = sum(1 for d in domains if d.get("risk_score", 0) >= 70)

                    console.print("\n[bold]Summary:[/bold]")
                    console.print(f"  Total domains found: {total}")
                    console.print(f"  High risk domains: [red]{high_risk}[/red]")

                    if total > limit:
                        console.print(f"\n[dim]Showing {limit} of {total} total domains[/dim]")
                else:
                    console.print("[green]No brand infringement detected[/green]")
            else:
                console.print("[yellow]No monitoring results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in brand monitoring: {e}[/red]")
        sys.exit(1)


@monitor.command()
@click.argument("query")
@click.option("--days-back", type=int, default=30, help="Number of days to look back")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def registrant(ctx, query, days_back, limit, raw):
    """Monitor domains by registrant information.

    Track domain registrations by specific individuals or organizations.

    Example:
        domaintools monitor registrant "john.doe@example.com"
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
        kwargs = {"days_back": days_back, "limit": limit}

        with console.status(f"Monitoring registrant '{query}'..."):
            result = client.registrant_monitor(query, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Registrant Monitor: {query}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Registrant Monitor: {query}")
        else:
            console.print(f"\n[bold cyan]Registrant Monitor: '{query}'[/bold cyan]")
            console.print(f"[dim]Last {days_back} days[/dim]\n")

            if "domains" in result:
                domains = result["domains"]

                if domains:
                    from rich.table import Table

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Domain", style="cyan")
                    table.add_column("Registered", style="yellow")
                    table.add_column("Registrar", style="green")
                    table.add_column("Status", style="blue")

                    for domain_info in domains[:limit]:
                        status = domain_info.get("status", "active")
                        status_color = "green" if status == "active" else "red"

                        table.add_row(
                            domain_info.get("domain", "N/A"),
                            str(domain_info.get("created", "N/A")),
                            domain_info.get("registrar", "N/A")[:30],
                            f"[{status_color}]{status}[/{status_color}]",
                        )

                    console.print(table)

                    total = len(domains)
                    if total > limit:
                        console.print(f"\n[dim]Showing {limit} of {total} total domains[/dim]")
                else:
                    console.print("[yellow]No domains found for this registrant[/yellow]")
            else:
                console.print("[yellow]No monitoring results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in registrant monitoring: {e}[/red]")
        sys.exit(1)


@monitor.command()
@click.argument("nameserver")
@click.option("--days-back", type=int, default=30, help="Number of days to look back")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def nameserver(ctx, nameserver, days_back, limit, raw):
    """Monitor domains using a specific nameserver.

    Track new domains that start using a particular nameserver.

    Example:
        domaintools monitor nameserver "ns1.suspicious.com"
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
        kwargs = {"days_back": days_back, "limit": limit}

        with console.status(f"Monitoring nameserver '{nameserver}'..."):
            result = client.name_server_monitor(nameserver, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Nameserver Monitor: {nameserver}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Nameserver Monitor: {nameserver}")
        else:
            console.print(f"\n[bold cyan]Nameserver Monitor: '{nameserver}'[/bold cyan]")
            console.print(f"[dim]Last {days_back} days[/dim]\n")

            if "domains" in result:
                domains = result["domains"]

                if domains:
                    # Separate new and existing domains
                    new_domains = [d for d in domains if d.get("is_new", False)]
                    existing_domains = [d for d in domains if not d.get("is_new", False)]

                    if new_domains:
                        console.print("[bold red]⚠ New Domains:[/bold red]")
                        from rich.table import Table

                        new_table = Table(show_header=True, header_style="bold magenta")
                        new_table.add_column("Domain", style="cyan")
                        new_table.add_column("First Seen", style="yellow")
                        new_table.add_column("Registrar", style="green")

                        for domain_info in new_domains[: limit // 2]:
                            new_table.add_row(
                                domain_info.get("domain", "N/A"),
                                str(domain_info.get("first_seen", "N/A")),
                                domain_info.get("registrar", "N/A")[:30],
                            )

                        console.print(new_table)

                    if existing_domains and limit > len(new_domains):
                        console.print("\n[bold]Existing Domains:[/bold]")
                        from rich.table import Table

                        existing_table = Table(show_header=True, header_style="bold blue")
                        existing_table.add_column("Domain", style="cyan")
                        existing_table.add_column("First Seen", style="yellow")
                        existing_table.add_column("Last Seen", style="green")

                        remaining_limit = limit - len(new_domains)
                        for domain_info in existing_domains[:remaining_limit]:
                            existing_table.add_row(
                                domain_info.get("domain", "N/A"),
                                str(domain_info.get("first_seen", "N/A")),
                                str(domain_info.get("last_seen", "N/A")),
                            )

                        console.print(existing_table)

                    # Summary
                    console.print("\n[bold]Summary:[/bold]")
                    console.print(f"  Total domains: {len(domains)}")
                    console.print(f"  New domains: [red]{len(new_domains)}[/red]")
                    console.print(f"  Existing domains: {len(existing_domains)}")
                else:
                    console.print("[yellow]No domains found using this nameserver[/yellow]")
            else:
                console.print("[yellow]No monitoring results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in nameserver monitoring: {e}[/red]")
        sys.exit(1)
