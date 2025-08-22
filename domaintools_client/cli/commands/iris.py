"""Iris API commands."""

import sys

import click


@click.group()
@click.pass_context
def iris(ctx):
    """Iris API commands for advanced domain intelligence."""
    pass


@iris.command()
@click.argument("domain")
@click.option("--include-whois", is_flag=True, help="Include WHOIS data")
@click.option("--include-dns", is_flag=True, help="Include DNS data")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def investigate(ctx, domain, include_whois, include_dns, raw):
    """Iris Investigate - comprehensive domain investigation.

    Provides deep intelligence on domains including risk scoring,
    infrastructure connections, and threat indicators.

    Example:
        domaintools iris investigate suspicious-domain.com --include-whois
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
        kwargs = {}
        if include_whois:
            kwargs["include_whois"] = True
        if include_dns:
            kwargs["include_dns"] = True

        with console.status(f"Investigating {domain} with Iris..."):
            result = client.iris_investigate(domain, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Iris Investigation: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Iris Investigation: {domain}")
        else:
            # Format Iris investigation results
            console.print(f"\n[bold cyan]Iris Investigation: {domain}[/bold cyan]\n")

            # Risk score
            if "risk_score" in result:
                score = result["risk_score"]
                if score < 30:
                    color = "green"
                elif score < 70:
                    color = "yellow"
                else:
                    color = "red"
                console.print(f"[bold]Risk Score:[/bold] [{color}]{score}[/{color}]\n")

            # Infrastructure
            if "infrastructure" in result:
                infra = result["infrastructure"]
                console.print("[bold]Infrastructure:[/bold]")
                console.print(f"  IP Addresses: {infra.get('ip_count', 0)}")
                console.print(f"  Nameservers: {infra.get('nameserver_count', 0)}")
                console.print(f"  Mail Servers: {infra.get('mailserver_count', 0)}")

            # Connected domains
            if "connected_domains" in result:
                connected = result["connected_domains"]
                if connected:
                    console.print("\n[bold]Connected Domains:[/bold]")
                    for domain_info in connected[:10]:
                        console.print(
                            f"  • {domain_info.get('domain', 'N/A')} (Score: {domain_info.get('risk_score', 'N/A')})"
                        )

                    if len(connected) > 10:
                        console.print(f"  [dim]... and {len(connected) - 10} more[/dim]")

            # Threat indicators
            if "threat_indicators" in result:
                threats = result["threat_indicators"]
                if threats:
                    console.print("\n[bold red]Threat Indicators:[/bold red]")
                    for threat in threats:
                        console.print(f"  ⚠ {threat}")
    except Exception as e:
        console.print(f"[red]Error in Iris investigation: {e}[/red]")
        sys.exit(1)


@iris.command()
@click.argument("domain")
@click.option(
    "--data-type",
    type=click.Choice(["whois", "dns", "ssl", "all"]),
    default="all",
    help="Type of data to enrich",
)
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def enrich(ctx, domain, data_type, raw):
    """Iris Enrich - enhance domain data with additional intelligence.

    Enriches domain information with comprehensive data points including
    WHOIS, DNS, SSL certificates, and more.

    Example:
        domaintools iris enrich example.com --data-type whois
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
        kwargs = {"data_type": data_type} if data_type != "all" else {}

        with console.status(f"Enriching {domain} data..."):
            result = client.iris_enrich(domain, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Iris Enrich: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Iris Enrich: {domain}")
        else:
            # Format enrichment results
            console.print(f"\n[bold cyan]Iris Enrichment: {domain}[/bold cyan]\n")

            # WHOIS enrichment
            if "whois" in result:
                whois = result["whois"]
                console.print("[bold]WHOIS Data:[/bold]")
                console.print(f"  Registrant: {whois.get('registrant', 'N/A')}")
                console.print(f"  Registrar: {whois.get('registrar', 'N/A')}")
                console.print(f"  Created: {whois.get('created', 'N/A')}")
                console.print(f"  Expires: {whois.get('expires', 'N/A')}")

            # DNS enrichment
            if "dns" in result:
                dns = result["dns"]
                console.print("\n[bold]DNS Data:[/bold]")
                if "a_records" in dns:
                    console.print(f"  A Records: {', '.join(dns['a_records'])}")
                if "mx_records" in dns:
                    console.print(f"  MX Records: {', '.join(dns['mx_records'])}")
                if "ns_records" in dns:
                    console.print(f"  NS Records: {', '.join(dns['ns_records'])}")

            # SSL enrichment
            if "ssl" in result:
                ssl = result["ssl"]
                console.print("\n[bold]SSL Certificate:[/bold]")
                console.print(f"  Issuer: {ssl.get('issuer', 'N/A')}")
                console.print(f"  Subject: {ssl.get('subject', 'N/A')}")
                console.print(f"  Valid From: {ssl.get('valid_from', 'N/A')}")
                console.print(f"  Valid To: {ssl.get('valid_to', 'N/A')}")
    except Exception as e:
        console.print(f"[red]Error in Iris enrichment: {e}[/red]")
        sys.exit(1)


@iris.command()
@click.option("--days", type=int, default=7, help="Number of days to look back")
@click.option("--risk-threshold", type=int, default=70, help="Minimum risk score threshold")
@click.option("--limit", type=int, default=100, help="Maximum number of results")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def detect(ctx, days, risk_threshold, limit, raw):
    """Iris Detect - identify newly observed malicious domains.

    Detects and reports on newly registered or activated domains that
    exhibit suspicious characteristics or match threat patterns.

    Example:
        domaintools iris detect --days 30 --risk-threshold 80
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
        kwargs = {"days_back": days, "risk_score_threshold": risk_threshold, "limit": limit}

        with console.status(f"Detecting threats from last {days} days..."):
            result = client.iris_detect(**kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, "Iris Detect Results")
        elif output_format == "tree":
            formatter.format_tree(result, "Iris Detect Results")
        else:
            # Format detection results
            console.print("\n[bold cyan]Iris Threat Detection[/bold cyan]")
            console.print(f"[dim]Last {days} days, Risk threshold: {risk_threshold}[/dim]\n")

            if "detected_domains" in result:
                domains = result["detected_domains"]

                if domains:
                    from rich.table import Table

                    table = Table(title="Detected Threats")
                    table.add_column("Domain", style="cyan")
                    table.add_column("Risk Score", style="red")
                    table.add_column("First Seen", style="yellow")
                    table.add_column("Threat Type", style="magenta")

                    for domain_info in domains[:limit]:
                        risk_score = domain_info.get("risk_score", 0)
                        risk_color = "red" if risk_score >= 80 else "yellow"

                        table.add_row(
                            domain_info.get("domain", "N/A"),
                            f"[{risk_color}]{risk_score}[/{risk_color}]",
                            str(domain_info.get("first_seen", "N/A")),
                            domain_info.get("threat_type", "Unknown"),
                        )

                    console.print(table)

                    total = len(domains)
                    if total > limit:
                        console.print(f"\n[dim]Showing {limit} of {total} detected threats[/dim]")
                else:
                    console.print("[green]No threats detected in the specified timeframe[/green]")
            else:
                console.print("[yellow]No detection results available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in Iris detection: {e}[/red]")
        sys.exit(1)
