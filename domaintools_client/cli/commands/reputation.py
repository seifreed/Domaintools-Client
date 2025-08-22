"""Reputation CLI commands."""

import sys

import click


@click.group()
@click.pass_context
def reputation(ctx):
    """Domain reputation commands."""
    pass


@reputation.command()
@click.argument("domain")
@click.option("--include-reasons", is_flag=True, help="Include detailed risk reasons")
@click.option("--raw", is_flag=True, help="Show raw JSON output")
@click.pass_context
def check(ctx, domain, include_reasons, raw):
    """Check domain reputation and risk score.

    Get a comprehensive risk assessment for a domain including
    reputation score and threat indicators.

    Example:
        domaintools reputation check suspicious-site.com --include-reasons
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
        if include_reasons:
            kwargs["include_reasons"] = True

        with console.status(f"Checking reputation for {domain}..."):
            result = client.reputation(domain, **kwargs)

        if raw or output_format == "json":
            formatter.format_json(result, f"Reputation: {domain}")
        elif output_format == "tree":
            formatter.format_tree(result, f"Reputation: {domain}")
        else:
            console.print(f"\n[bold cyan]Domain Reputation: {domain}[/bold cyan]\n")

            # Risk score with visual indicator
            if "risk_score" in result:
                score = result["risk_score"]

                # Determine risk level and color
                if score < 30:
                    risk_level = "LOW RISK"
                    risk_color = "green"
                    emoji = "✅"
                elif score < 70:
                    risk_level = "MEDIUM RISK"
                    risk_color = "yellow"
                    emoji = "⚠️"
                else:
                    risk_level = "HIGH RISK"
                    risk_color = "red"
                    emoji = "🚨"

                # Create risk score bar
                bar_length = 50
                filled_length = int(bar_length * score / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)

                from rich.panel import Panel

                risk_text = f"{emoji} [bold {risk_color}]{risk_level}[/bold {risk_color}]\n\n"
                risk_text += f"Risk Score: [{risk_color}]{score}/100[/{risk_color}]\n"
                risk_text += f"[{risk_color}]{bar}[/{risk_color}]"

                console.print(Panel(risk_text, title="Risk Assessment", border_style=risk_color))

            # Risk factors
            if "risk_factors" in result and result["risk_factors"]:
                console.print("\n[bold]Risk Factors:[/bold]")
                for factor in result["risk_factors"]:
                    console.print(f"  • [red]{factor}[/red]")

            # Threat indicators
            if "threat_indicators" in result and result["threat_indicators"]:
                console.print("\n[bold]Threat Indicators:[/bold]")
                for indicator in result["threat_indicators"]:
                    console.print(f"  ⚠ [yellow]{indicator}[/yellow]")

            # Categories
            if "categories" in result and result["categories"]:
                console.print("\n[bold]Categories:[/bold]")
                categories = result["categories"]
                if isinstance(categories, list):
                    for category in categories:
                        console.print(f"  • {category}")
                else:
                    console.print(f"  {categories}")

            # Detailed reasons if requested
            if include_reasons and "risk_reasons" in result:
                reasons = result["risk_reasons"]
                if reasons:
                    from rich.table import Table

                    reasons_table = Table(title="Detailed Risk Analysis", show_header=True)
                    reasons_table.add_column("Factor", style="yellow")
                    reasons_table.add_column("Score Impact", style="red")
                    reasons_table.add_column("Description", style="white")

                    for reason in reasons:
                        reasons_table.add_row(
                            reason.get("factor", "N/A"),
                            str(reason.get("score_impact", "N/A")),
                            reason.get("description", "N/A"),
                        )

                    console.print("\n")
                    console.print(reasons_table)

            # Recommendations
            if "recommendations" in result:
                console.print("\n[bold]Recommendations:[/bold]")
                for rec in result["recommendations"]:
                    console.print(f"  → {rec}")
    except Exception as e:
        console.print(f"[red]Error checking reputation: {e}[/red]")
        sys.exit(1)


@reputation.command()
@click.argument("domains", nargs=-1, required=True)
@click.option("--threshold", type=int, default=70, help="Risk score threshold for alerts")
@click.option("--export", type=click.Path(), help="Export results to CSV file")
@click.pass_context
def batch_check(ctx, domains, threshold, export):
    """Check reputation for multiple domains.

    Example:
        domaintools reputation batch-check domain1.com domain2.com domain3.com
    """
    client = ctx.obj["client"]
    console = ctx.obj["console"]

    if not client:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Run 'domaintools config set' to configure credentials")
        sys.exit(1)

    results = []
    high_risk_domains = []

    with console.status(f"Checking {len(domains)} domains...") as status:
        for i, domain in enumerate(domains, 1):
            status.update(f"Checking domain {i}/{len(domains)}: {domain}")

            try:
                result = client.reputation(domain)
                risk_score = result.get("risk_score", 0)

                domain_result = {
                    "domain": domain,
                    "risk_score": risk_score,
                    "risk_level": (
                        "High" if risk_score >= 70 else "Medium" if risk_score >= 30 else "Low"
                    ),
                    "categories": (
                        ", ".join(result.get("categories", [])) if "categories" in result else "N/A"
                    ),
                }

                results.append(domain_result)

                if risk_score >= threshold:
                    high_risk_domains.append(domain_result)

            except Exception as e:
                results.append(
                    {
                        "domain": domain,
                        "risk_score": "Error",
                        "risk_level": "Error",
                        "categories": str(e),
                    }
                )

    # Display results table
    from rich.table import Table

    table = Table(title="Batch Reputation Check Results", show_header=True)
    table.add_column("Domain", style="cyan")
    table.add_column("Risk Score", style="white")
    table.add_column("Risk Level", style="white")
    table.add_column("Categories", style="yellow")

    for result in results:
        score = result["risk_score"]
        level = result["risk_level"]

        # Color coding for risk levels
        if level == "High":
            level_display = f"[red]{level}[/red]"
            score_display = f"[red]{score}[/red]" if score != "Error" else "[red]Error[/red]"
        elif level == "Medium":
            level_display = f"[yellow]{level}[/yellow]"
            score_display = f"[yellow]{score}[/yellow]"
        elif level == "Low":
            level_display = f"[green]{level}[/green]"
            score_display = f"[green]{score}[/green]"
        else:
            level_display = f"[dim]{level}[/dim]"
            score_display = f"[dim]{score}[/dim]"

        table.add_row(result["domain"], score_display, level_display, result["categories"][:50])

    console.print("\n")
    console.print(table)

    # Show high-risk summary
    if high_risk_domains:
        console.print(
            f"\n[bold red]⚠ Warning: {len(high_risk_domains)} domains exceed risk threshold ({threshold}):[/bold red]"
        )
        for domain in high_risk_domains:
            console.print(f"  • {domain['domain']} (Score: {domain['risk_score']})")

    # Export to CSV if requested
    if export:
        import csv

        try:
            with open(export, "w", newline="") as csvfile:
                fieldnames = ["domain", "risk_score", "risk_level", "categories"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            console.print(f"\n[green]Results exported to {export}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting results: {e}[/red]")
