"""Domain-related CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def domain(ctx):
    """Domain information commands."""
    pass


@domain.command()
@click.argument("domain")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def profile(ctx, domain, raw):
    """Get comprehensive domain profile information.

    Example:
        domaintools domain profile example.com
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
        with console.status(f"Fetching profile for {domain}..."):
            result = client.domain_profile(domain)

        if raw or output_format == "json":
            formatter.format_json(result, f"Domain Profile: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Domain Profile: {domain}")
        else:
            formatter.format_domain_profile(result)
    except Exception as e:
        console.print(f"[red]Error fetching domain profile: {e}[/red]")
        sys.exit(1)


@domain.command()
@click.argument("domain")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def whois(ctx, domain, raw):
    """Get WHOIS information for a domain.

    Example:
        domaintools domain whois example.com
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
        with console.status(f"Fetching WHOIS for {domain}..."):
            result = client.whois(domain)

        if raw or output_format == "json":
            formatter.format_json(result, f"WHOIS: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"WHOIS: {domain}")
        else:
            # Format WHOIS data in a readable way
            if "whois" in result:
                whois_data = result["whois"]
                console.print(f"\n[bold cyan]WHOIS Information for {domain}[/bold cyan]\n")

                if isinstance(whois_data, dict):
                    for key, value in whois_data.items():
                        console.print(f"[yellow]{key}:[/yellow] {value}")
                else:
                    console.print(whois_data)
    except Exception as e:
        console.print(f"[red]Error fetching WHOIS: {e}[/red]")
        sys.exit(1)


@domain.command()
@click.argument("domain")
@click.option("--limit", "-l", type=int, default=100, help="Maximum number of records")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def history(ctx, domain, limit, raw):
    """Get WHOIS history for a domain.

    Example:
        domaintools domain history example.com --limit 50
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
            # Format history in a table
            if "history" in result and result["history"]:
                from rich.table import Table

                table = Table(title=f"WHOIS History for {domain}")
                table.add_column("Date", style="cyan")
                table.add_column("Registrant", style="yellow")
                table.add_column("Registrar", style="green")

                for record in result["history"][:limit]:
                    table.add_row(
                        str(record.get("date", "N/A")),
                        str(record.get("registrant", "N/A")),
                        str(record.get("registrar", "N/A")),
                    )

                console.print(table)
            else:
                console.print("[yellow]No history records found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error fetching WHOIS history: {e}[/red]")
        sys.exit(1)


@domain.command()
@click.argument("domain")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def parsed(ctx, domain, raw):
    """Get parsed WHOIS data for a domain.

    Example:
        domaintools domain parsed example.com
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
            # Format parsed data in a structured way
            console.print(f"\n[bold cyan]Parsed WHOIS for {domain}[/bold cyan]\n")

            if "parsed_whois" in result:
                parsed = result["parsed_whois"]

                # Contacts
                if "contacts" in parsed:
                    from rich.table import Table

                    contacts_table = Table(title="Contacts")
                    contacts_table.add_column("Type", style="yellow")
                    contacts_table.add_column("Name", style="white")
                    contacts_table.add_column("Email", style="cyan")

                    for contact_type, contact_info in parsed["contacts"].items():
                        contacts_table.add_row(
                            contact_type,
                            contact_info.get("name", "N/A"),
                            contact_info.get("email", "N/A"),
                        )

                    console.print(contacts_table)

                # Registration dates
                if "registration" in parsed:
                    reg = parsed["registration"]
                    console.print("\n[bold]Registration Information:[/bold]")
                    console.print(f"  Created: {reg.get('created', 'N/A')}")
                    console.print(f"  Updated: {reg.get('updated', 'N/A')}")
                    console.print(f"  Expires: {reg.get('expires', 'N/A')}")

                # Nameservers
                if "nameservers" in parsed:
                    console.print("\n[bold]Nameservers:[/bold]")
                    for ns in parsed["nameservers"]:
                        console.print(f"  • {ns}")
    except Exception as e:
        console.print(f"[red]Error fetching parsed WHOIS: {e}[/red]")
        sys.exit(1)
