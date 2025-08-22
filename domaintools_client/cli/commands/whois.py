"""WHOIS-related CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def whois(ctx):
    """WHOIS information commands."""
    pass


@whois.command()
@click.argument("domain")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def lookup(ctx, domain, raw):
    """Get current WHOIS information for a domain.

    Example:
        domaintools whois lookup example.com
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
        with console.status(f"Looking up WHOIS for {domain}..."):
            result = client.whois(domain)

        if raw or output_format == "json":
            formatter.format_json(result, f"WHOIS: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"WHOIS: {domain}")
        else:
            console.print(f"\n[bold cyan]WHOIS Information: {domain}[/bold cyan]\n")

            if "record" in result:
                # Display raw WHOIS record
                console.print(result["record"])
            elif "whois" in result:
                # Display parsed WHOIS data
                whois_data = result["whois"]
                for key, value in whois_data.items():
                    if value:
                        console.print(f"[yellow]{key.replace('_', ' ').title()}:[/yellow] {value}")
    except Exception as e:
        console.print(f"[red]Error fetching WHOIS: {e}[/red]")
        sys.exit(1)


@whois.command()
@click.argument("domain")
@click.option("--limit", "-l", type=int, default=50, help="Maximum number of historical records")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def history(ctx, domain, limit, raw):
    """Get historical WHOIS records for a domain.

    Example:
        domaintools whois history example.com --limit 100
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
        with console.status(f"Fetching WHOIS history for {domain}..."):
            result = client.whois_history(domain, limit=limit)

        if raw or output_format == "json":
            formatter.format_json(result, f"WHOIS History: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"WHOIS History: {domain}")
        else:
            console.print(f"\n[bold cyan]WHOIS History: {domain}[/bold cyan]\n")

            if "history" in result and result["history"]:
                from rich.table import Table

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Date", style="cyan")
                table.add_column("Registrant", style="yellow")
                table.add_column("Email", style="green")
                table.add_column("Registrar", style="blue")

                for record in result["history"][:limit]:
                    table.add_row(
                        str(record.get("date", "N/A")),
                        str(record.get("registrant", "N/A"))[:30],
                        str(record.get("email", "N/A"))[:30],
                        str(record.get("registrar", "N/A"))[:30],
                    )

                console.print(table)

                total = result.get("record_count", len(result["history"]))
                if total > limit:
                    console.print(f"\n[dim]Showing {limit} of {total} historical records[/dim]")
            else:
                console.print("[yellow]No historical WHOIS records found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error fetching WHOIS history: {e}[/red]")
        sys.exit(1)


@whois.command()
@click.argument("domain")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def parsed(ctx, domain, raw):
    """Get parsed and structured WHOIS data.

    Example:
        domaintools whois parsed example.com
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
        with console.status(f"Fetching parsed WHOIS for {domain}..."):
            result = client.parsed_whois(domain)

        if raw or output_format == "json":
            formatter.format_json(result, f"Parsed WHOIS: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Parsed WHOIS: {domain}")
        else:
            console.print(f"\n[bold cyan]Parsed WHOIS: {domain}[/bold cyan]\n")

            if "parsed_whois" in result:
                parsed = result["parsed_whois"]

                # Registration dates
                if "registration" in parsed:
                    from rich.panel import Panel

                    reg = parsed["registration"]
                    reg_text = f"[bold]Created:[/bold] {reg.get('created', 'N/A')}\n"
                    reg_text += f"[bold]Updated:[/bold] {reg.get('updated', 'N/A')}\n"
                    reg_text += f"[bold]Expires:[/bold] {reg.get('expires', 'N/A')}"
                    console.print(Panel(reg_text, title="Registration", border_style="green"))

                # Contacts
                if "contacts" in parsed:
                    from rich.table import Table

                    contacts_table = Table(title="Contacts", show_header=True)
                    contacts_table.add_column("Type", style="yellow")
                    contacts_table.add_column("Name", style="white")
                    contacts_table.add_column("Organization", style="cyan")
                    contacts_table.add_column("Email", style="green")

                    for contact_type, contact_info in parsed["contacts"].items():
                        if contact_info:
                            contacts_table.add_row(
                                contact_type.title(),
                                contact_info.get("name", "N/A"),
                                contact_info.get("org", "N/A"),
                                contact_info.get("email", "N/A"),
                            )

                    console.print(contacts_table)

                # Nameservers
                if "nameservers" in parsed and parsed["nameservers"]:
                    console.print("\n[bold]Nameservers:[/bold]")
                    for ns in parsed["nameservers"]:
                        console.print(f"  • {ns}")

                # Status flags
                if "status" in parsed and parsed["status"]:
                    console.print("\n[bold]Status Flags:[/bold]")
                    for status in parsed["status"]:
                        console.print(f"  • {status}")
    except Exception as e:
        console.print(f"[red]Error fetching parsed WHOIS: {e}[/red]")
        sys.exit(1)
