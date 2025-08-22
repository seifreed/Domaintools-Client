#!/usr/bin/env python3
"""Code Quality Checker for DomainTools Client."""

import subprocess  # nosec B404 - subprocess is used safely with controlled inputs
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def run_command(command: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )  # nosec B603 - command list is trusted
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_bandit() -> bool:
    """Run Bandit security analysis."""
    console.print("\n[bold cyan]Running Security Analysis (Bandit)...[/bold cyan]")

    files = ["domaintools_client/", "dt-cli.py", "dt.py", "examples/"]

    exit_code, stdout, stderr = run_command(["./venv/bin/bandit", "-r"] + files + ["-f", "json"])

    # Parse results
    if "No issues identified" in stderr or exit_code == 0:
        console.print("[green]✅ Security Check: PASSED[/green]")
        console.print("   No security vulnerabilities found")
        return True
    else:
        console.print("[red]❌ Security Check: FAILED[/red]")
        console.print("   Issues found. Run 'bandit -r domaintools_client/' for details")
        return False


def check_ruff() -> bool:
    """Run Ruff code quality analysis."""
    console.print("\n[bold cyan]Running Code Quality Analysis (Ruff)...[/bold cyan]")

    files = ["domaintools_client/", "dt-cli.py", "dt.py", "examples/"]

    exit_code, stdout, stderr = run_command(["./venv/bin/ruff", "check"] + files)

    if exit_code == 0 and "All checks passed" in stdout:
        console.print("[green]✅ Code Quality Check: PASSED[/green]")
        console.print("   All code quality checks passed")
        return True
    else:
        console.print("[red]❌ Code Quality Check: FAILED[/red]")
        console.print("   Issues found. Run 'ruff check domaintools_client/' for details")
        return False


def get_code_stats() -> dict:
    """Get code statistics."""
    stats = {
        "python_files": 0,
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
    }

    # Find all Python files
    project_dir = Path(__file__).parent
    python_files: list[Path] = []

    for pattern in ["domaintools_client/**/*.py", "*.py", "examples/*.py"]:
        python_files.extend(project_dir.glob(pattern))

    # Exclude venv
    python_files = [f for f in python_files if "venv" not in str(f)]
    stats["python_files"] = len(python_files)

    # Count lines
    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
                stats["total_lines"] += len(lines)

                for line in lines:
                    line = line.strip()
                    if not line:
                        stats["blank_lines"] += 1
                    elif line.startswith("#"):
                        stats["comment_lines"] += 1
                    else:
                        stats["code_lines"] += 1
        except OSError as e:
            # Log file read errors but continue processing
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return stats


def display_results(bandit_passed: bool, ruff_passed: bool, stats: dict) -> None:
    """Display quality check results."""
    # Overall status
    all_passed = bandit_passed and ruff_passed

    if all_passed:
        console.print("\n")
        panel = Panel.fit(
            "[bold green]✅ CODE QUALITY: 100%[/bold green]\n\n"
            "All quality checks passed successfully!",
            title="[bold]Quality Report[/bold]",
            border_style="green",
        )
        console.print(panel)
    else:
        console.print("\n")
        panel = Panel.fit(
            "[bold red]❌ QUALITY CHECKS FAILED[/bold red]\n\n"
            "Please fix the issues before committing.",
            title="[bold]Quality Report[/bold]",
            border_style="red",
        )
        console.print(panel)

    # Statistics table
    console.print("\n[bold cyan]Code Statistics:[/bold cyan]")

    table = Table(box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="white")

    table.add_row("Python Files", str(stats["python_files"]))
    table.add_row("Total Lines", f"{stats['total_lines']:,}")
    table.add_row("Code Lines", f"{stats['code_lines']:,}")
    table.add_row("Comment Lines", f"{stats['comment_lines']:,}")
    table.add_row("Blank Lines", f"{stats['blank_lines']:,}")

    if stats["total_lines"] > 0:
        code_percentage = (stats["code_lines"] / stats["total_lines"]) * 100
        table.add_row("Code Density", f"{code_percentage:.1f}%")

    console.print(table)

    # Quality scores
    console.print("\n[bold cyan]Quality Scores:[/bold cyan]")

    scores_table = Table(box=box.ROUNDED)
    scores_table.add_column("Category", style="cyan")
    scores_table.add_column("Score", justify="center", style="white")
    scores_table.add_column("Status", justify="center")

    scores_table.add_row(
        "Security",
        "100%" if bandit_passed else "0%",
        "[green]✅ PASSED[/green]" if bandit_passed else "[red]❌ FAILED[/red]",
    )
    scores_table.add_row(
        "Code Quality",
        "100%" if ruff_passed else "0%",
        "[green]✅ PASSED[/green]" if ruff_passed else "[red]❌ FAILED[/red]",
    )
    scores_table.add_row(
        "Overall",
        "100%" if all_passed else "50%" if (bandit_passed or ruff_passed) else "0%",
        "[green]✅ PASSED[/green]" if all_passed else "[red]❌ FAILED[/red]",
    )

    console.print(scores_table)


def main():
    """Main entry point."""
    console.print("[bold]DomainTools Client - Code Quality Checker[/bold]\n")

    # Check if tools are installed
    tools = {"bandit": "./venv/bin/bandit", "ruff": "./venv/bin/ruff"}
    for tool_name, tool_path in tools.items():
        exit_code, _, _ = run_command([tool_path, "--version"])
        if exit_code != 0:
            console.print(f"[red]Error: {tool_name} is not installed[/red]")
            console.print(f"Install with: pip install {tool_name}")
            sys.exit(1)

    # Run checks
    bandit_passed = check_bandit()
    ruff_passed = check_ruff()
    stats = get_code_stats()

    # Display results
    display_results(bandit_passed, ruff_passed, stats)

    # Exit with appropriate code
    sys.exit(0 if (bandit_passed and ruff_passed) else 1)


if __name__ == "__main__":
    main()
