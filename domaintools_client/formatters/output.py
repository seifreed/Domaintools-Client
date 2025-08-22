"""Rich output formatters for DomainTools data."""

import json
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree


class OutputFormatter:
    """Formatter for rich output display."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize output formatter.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()

    def format_json(self, data: Dict[str, Any], title: str = "JSON Output") -> None:
        """Format and display JSON data with syntax highlighting.

        Args:
            data: Data to format
            title: Panel title
        """
        json_str = json.dumps(data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        panel = Panel(syntax, title=title, border_style="cyan")
        self.console.print(panel)

    def format_table(self, data: List[Dict[str, Any]], title: str = "Results") -> None:
        """Format data as a rich table.

        Args:
            data: List of dictionaries to display
            title: Table title
        """
        if not data:
            self.console.print("[yellow]No results found[/yellow]")
            return

        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta")

        # Add columns based on first item
        if data:
            for key in data[0].keys():
                table.add_column(key.replace("_", " ").title(), style="cyan")

        # Add rows
        for item in data:
            row = []
            for value in item.values():
                if isinstance(value, (dict, list)):
                    row.append(json.dumps(value, indent=2))
                else:
                    row.append(str(value))
            table.add_row(*row)

        self.console.print(table)

    def format_tree(self, data: Dict[str, Any], title: str = "Data Tree") -> None:
        """Format nested data as a tree structure.

        Args:
            data: Nested dictionary to display
            title: Tree title
        """
        tree = Tree(f"[bold cyan]{title}[/bold cyan]")
        self._build_tree(tree, data)
        self.console.print(tree)

    def _build_tree(
        self, tree: Tree, data: Any, max_depth: int = 10, current_depth: int = 0
    ) -> None:
        """Recursively build tree structure.

        Args:
            tree: Tree node to add to
            data: Data to add
            max_depth: Maximum tree depth
            current_depth: Current recursion depth
        """
        if current_depth >= max_depth:
            tree.add("[dim]...[/dim]")
            return

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and value:
                    branch = tree.add(f"[bold yellow]{key}[/bold yellow]")
                    self._build_tree(branch, value, max_depth, current_depth + 1)
                else:
                    tree.add(f"[green]{key}[/green]: {self._format_value(value)}")
        elif isinstance(data, list):
            for i, item in enumerate(data[:10]):  # Limit list items
                if isinstance(item, (dict, list)):
                    branch = tree.add(f"[bold blue][{i}][/bold blue]")
                    self._build_tree(branch, item, max_depth, current_depth + 1)
                else:
                    tree.add(f"[{i}]: {self._format_value(item)}")
            if len(data) > 10:
                tree.add(f"[dim]... and {len(data) - 10} more items[/dim]")

    def _format_value(self, value: Any) -> str:
        """Format a single value for display.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        if value is None:
            return "[dim]None[/dim]"
        elif isinstance(value, bool):
            return f"[cyan]{value}[/cyan]"
        elif isinstance(value, (int, float)):
            return f"[magenta]{value}[/magenta]"
        elif isinstance(value, str):
            if len(value) > 100:
                return f"{value[:100]}[dim]...[/dim]"
            return value
        else:
            return str(value)

    def format_domain_profile(self, profile: Dict[str, Any]) -> None:
        """Format and display domain profile data.

        Args:
            profile: Domain profile data
        """
        # Extract key information
        domain = profile.get("domain", {}).get("domain", "Unknown")

        # Create main panel
        self.console.print(
            Panel.fit(f"[bold cyan]Domain Profile: {domain}[/bold cyan]", border_style="cyan")
        )

        # Registration info
        if "registration" in profile:
            reg = profile["registration"]
            reg_table = Table(title="Registration Information", box=box.SIMPLE)
            reg_table.add_column("Field", style="yellow")
            reg_table.add_column("Value", style="white")

            reg_table.add_row("Created", str(reg.get("created", "N/A")))
            reg_table.add_row("Updated", str(reg.get("updated", "N/A")))
            reg_table.add_row("Expires", str(reg.get("expires", "N/A")))
            reg_table.add_row("Registrar", str(reg.get("registrar", "N/A")))

            self.console.print(reg_table)

        # WHOIS info
        if "whois" in profile:
            whois = profile["whois"]
            whois_table = Table(title="WHOIS Information", box=box.SIMPLE)
            whois_table.add_column("Field", style="yellow")
            whois_table.add_column("Value", style="white")

            if "registrant" in whois:
                whois_table.add_row("Registrant", whois["registrant"])
            if "admin" in whois:
                whois_table.add_row("Admin", whois["admin"])
            if "tech" in whois:
                whois_table.add_row("Tech", whois["tech"])

            self.console.print(whois_table)

        # DNS info
        if "dns" in profile:
            dns = profile["dns"]
            if "nameservers" in dns:
                ns_list = dns["nameservers"]
                self.console.print("\n[bold]Nameservers:[/bold]")
                for ns in ns_list:
                    self.console.print(f"  • {ns}")

        # Website info
        if "website" in profile:
            website = profile["website"]
            web_table = Table(title="Website Information", box=box.SIMPLE)
            web_table.add_column("Field", style="yellow")
            web_table.add_column("Value", style="white")

            web_table.add_row("Title", str(website.get("title", "N/A")))
            web_table.add_row("Server", str(website.get("server", "N/A")))
            web_table.add_row("Response Code", str(website.get("response_code", "N/A")))

            self.console.print(web_table)

    def format_search_results(self, results: Dict[str, Any], search_type: str = "Domain") -> None:
        """Format and display search results.

        Args:
            results: Search results data
            search_type: Type of search performed
        """
        self.console.print(
            Panel.fit(f"[bold cyan]{search_type} Search Results[/bold cyan]", border_style="cyan")
        )

        if "results" in results:
            items = results["results"]
            if not items:
                self.console.print("[yellow]No results found[/yellow]")
                return

            table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")

            # Dynamic column creation based on first result
            if items:
                for key in items[0].keys():
                    table.add_column(key.replace("_", " ").title(), style="cyan")

                for item in items[:20]:  # Limit to 20 results for display
                    row = []
                    for value in item.values():
                        if isinstance(value, (dict, list)):
                            row.append(json.dumps(value))
                        else:
                            row.append(str(value))
                    table.add_row(*row)

            self.console.print(table)

            if len(items) > 20:
                self.console.print(f"\n[dim]Showing 20 of {len(items)} total results[/dim]")

    def format_reputation(self, reputation: Dict[str, Any]) -> None:
        """Format and display reputation data.

        Args:
            reputation: Reputation data
        """
        domain = reputation.get("domain", "Unknown")
        risk_score = reputation.get("risk_score", 0)

        # Determine risk level color
        if risk_score < 30:
            risk_color = "green"
            risk_level = "Low"
        elif risk_score < 70:
            risk_color = "yellow"
            risk_level = "Medium"
        else:
            risk_color = "red"
            risk_level = "High"

        self.console.print(
            Panel(
                f"[bold]Domain:[/bold] {domain}\n"
                f"[bold]Risk Score:[/bold] [{risk_color}]{risk_score}[/{risk_color}] ({risk_level})",
                title="[bold cyan]Reputation Analysis[/bold cyan]",
                border_style="cyan",
            )
        )

        # Risk factors
        if "risk_factors" in reputation:
            self.console.print("\n[bold]Risk Factors:[/bold]")
            for factor in reputation["risk_factors"]:
                self.console.print(f"  • {factor}")

    def show_progress(self, task_name: str = "Processing") -> Progress:
        """Create and return a progress indicator.

        Args:
            task_name: Name of the task

        Returns:
            Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )


def format_domain_profile(profile: Dict[str, Any], console: Optional[Console] = None) -> None:
    """Convenience function to format domain profile.

    Args:
        profile: Domain profile data
        console: Optional console instance
    """
    formatter = OutputFormatter(console)
    formatter.format_domain_profile(profile)


def format_search_results(
    results: Dict[str, Any], search_type: str = "Domain", console: Optional[Console] = None
) -> None:
    """Convenience function to format search results.

    Args:
        results: Search results data
        search_type: Type of search
        console: Optional console instance
    """
    formatter = OutputFormatter(console)
    formatter.format_search_results(results, search_type)
