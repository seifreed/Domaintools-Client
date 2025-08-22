#!/usr/bin/env python3
"""DomainTools CLI Wrapper."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize console for rich output
console = Console()


class DomainToolsWrapper:
    """Wrapper for DomainTools CLI with enhanced configuration management."""

    def __init__(self):
        """Initialize the wrapper."""
        self.project_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.project_dir / "venv"
        self.config_loaded = False
        self.config_source = None
        self.api_credentials = {}

        # Configuration file search paths
        self.config_files = [
            self.project_dir / "config.yaml",
            self.project_dir / "config.yml",
            self.project_dir / "domaintools.yaml",
            self.project_dir / "domaintools.yml",
            Path.home() / ".domaintools" / "config.json",
        ]

        self.env_file = self.project_dir / ".env"

    def check_venv(self) -> bool:
        """Check if running in virtual environment."""
        return hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

    def activate_venv(self) -> None:
        """Activate virtual environment if it exists."""
        if not self.check_venv() and self.venv_dir.exists():
            # Add venv to Python path
            venv_site_packages = (
                self.venv_dir
                / "lib"
                / f"python{sys.version_info.major}.{sys.version_info.minor}"
                / "site-packages"
            )
            if venv_site_packages.exists():
                sys.path.insert(0, str(venv_site_packages))

    def load_env_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env_vars = {}
        if self.env_file.exists():
            try:
                with open(self.env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if (
                                value
                                and value != "your_api_key_here"
                                and value != "your_api_secret_here"
                            ):
                                env_vars[key] = value
                                os.environ[key] = value
            except Exception as e:
                console.print(f"[yellow]Warning: Error reading .env file: {e}[/yellow]")
        return env_vars

    def load_yaml_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config = {}
        try:
            with open(config_file) as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    # Extract API configuration
                    if "api" in yaml_data:
                        api_config = yaml_data["api"]
                        if api_config.get("key") and api_config["key"] != "your_api_key_here":
                            config["DOMAINTOOLS_API_KEY"] = api_config["key"]
                        if (
                            api_config.get("secret")
                            and api_config["secret"] != "your_api_secret_here"
                        ):
                            config["DOMAINTOOLS_API_SECRET"] = api_config["secret"]
                        if api_config.get("url"):
                            config["DOMAINTOOLS_API_URL"] = api_config["url"]

                    # Extract settings
                    if "settings" in yaml_data:
                        settings = yaml_data["settings"]
                        if "timeout" in settings:
                            config["DOMAINTOOLS_TIMEOUT"] = str(settings["timeout"])
                        if "max_retries" in settings:
                            config["DOMAINTOOLS_MAX_RETRIES"] = str(settings["max_retries"])
                        if "output_format" in settings:
                            config["DOMAINTOOLS_OUTPUT_FORMAT"] = settings["output_format"]
        except Exception as e:
            console.print(f"[yellow]Warning: Error reading YAML config: {e}[/yellow]")
        return config

    def load_json_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config = {}
        try:
            with open(config_file) as f:
                json_data = json.load(f)
                if json_data:
                    if json_data.get("api_key") and json_data["api_key"] != "your_api_key_here":
                        config["DOMAINTOOLS_API_KEY"] = json_data["api_key"]
                    if (
                        json_data.get("api_secret")
                        and json_data["api_secret"] != "your_api_secret_here"
                    ):
                        config["DOMAINTOOLS_API_SECRET"] = json_data["api_secret"]
                    if json_data.get("api_url"):
                        config["DOMAINTOOLS_API_URL"] = json_data["api_url"]
                    if "timeout" in json_data:
                        config["DOMAINTOOLS_TIMEOUT"] = str(json_data["timeout"])
                    if "max_retries" in json_data:
                        config["DOMAINTOOLS_MAX_RETRIES"] = str(json_data["max_retries"])
                    if "output_format" in json_data:
                        config["DOMAINTOOLS_OUTPUT_FORMAT"] = json_data["output_format"]
        except Exception as e:
            console.print(f"[yellow]Warning: Error reading JSON config: {e}[/yellow]")
        return config

    def load_configuration(self) -> bool:
        """Load configuration from all available sources."""
        # 1. Load from .env file
        env_config = self.load_env_file()
        if env_config.get("DOMAINTOOLS_API_KEY"):
            self.config_loaded = True
            self.config_source = ".env file"
            self.api_credentials = env_config
            return True

        # 2. Check environment variables
        if os.getenv("DOMAINTOOLS_API_KEY"):
            self.config_loaded = True
            self.config_source = "environment variables"
            self.api_credentials = {
                "DOMAINTOOLS_API_KEY": os.getenv("DOMAINTOOLS_API_KEY"),
                "DOMAINTOOLS_API_SECRET": os.getenv("DOMAINTOOLS_API_SECRET"),
            }
            return True

        # 3. Load from YAML/JSON config files
        for config_file in self.config_files:
            if config_file.exists():
                if config_file.suffix in [".yaml", ".yml"]:
                    config = self.load_yaml_config(config_file)
                elif config_file.suffix == ".json":
                    config = self.load_json_config(config_file)
                else:
                    continue

                if config.get("DOMAINTOOLS_API_KEY"):
                    # Set environment variables
                    for key, value in config.items():
                        os.environ[key] = value

                    self.config_loaded = True
                    self.config_source = str(config_file.name)
                    self.api_credentials = config
                    return True

        return False

    def show_configuration_help(self) -> None:
        """Show help for configuring the tool."""
        panel = Panel.fit(
            "[bold red]No API configuration found![/bold red]\n\n"
            "[yellow]Please configure your DomainTools API credentials using one of these methods:[/yellow]\n\n"
            "[bold]1. Copy and edit the environment file:[/bold]\n"
            f"   cp {self.project_dir}/.env.example {self.project_dir}/.env\n"
            "   # Edit .env with your API credentials\n\n"
            "[bold]2. Copy and edit the YAML configuration:[/bold]\n"
            f"   cp {self.project_dir}/config.yaml.example {self.project_dir}/config.yaml\n"
            "   # Edit config.yaml with your API credentials\n\n"
            "[bold]3. Run the configuration wizard:[/bold]\n"
            "   python dt-cli.py config set\n\n"
            "[bold]4. Set environment variables:[/bold]\n"
            "   export DOMAINTOOLS_API_KEY=your_key\n"
            "   export DOMAINTOOLS_API_SECRET=your_secret",
            title="Configuration Required",
            border_style="red",
        )
        console.print(panel)

    def show_status(self) -> None:
        """Show current configuration status."""
        table = Table(title="DomainTools CLI Configuration Status", box=box.ROUNDED)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        # Python version
        table.add_row(
            "Python Version",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

        # Virtual environment
        venv_status = "Active" if self.check_venv() else "Not active"
        table.add_row("Virtual Environment", venv_status)

        # Configuration
        if self.config_loaded:
            table.add_row("Configuration", f"[green]Loaded from {self.config_source}[/green]")
            if self.api_credentials.get("DOMAINTOOLS_API_KEY"):
                api_key = self.api_credentials["DOMAINTOOLS_API_KEY"]
                masked_key = api_key[:10] + "..." if len(api_key) > 10 else "***"
                table.add_row("API Key", masked_key)
        else:
            table.add_row("Configuration", "[red]Not configured[/red]")

        console.print(table)

    def run_cli(self, args: List[str]) -> int:
        """Run the DomainTools CLI with the given arguments."""
        # Add project directory to Python path
        sys.path.insert(0, str(self.project_dir))

        try:
            # Import and run the CLI
            from domaintools_client.cli.main import cli

            # Remove the script name from arguments
            sys.argv = ["domaintools"] + args

            # Run the CLI
            cli(standalone_mode=False)
            return 0

        except SystemExit as e:
            return int(e.code) if e.code is not None else 0
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            return 130
        except Exception as e:
            if "--debug" in args or os.getenv("DEBUG"):
                console.print_exception()
            else:
                console.print(f"[red]Error: {e}[/red]")
            return 1

    def main(self) -> int:
        """Main entry point for the wrapper."""
        # Get command-line arguments
        args = sys.argv[1:]

        # Check for help or version
        if not args or "--help" in args or "-h" in args:
            if not args:
                args = ["--help"]

        # Check for status command
        if args and args[0] == "status":
            self.load_configuration()
            self.show_status()
            return 0

        # Load configuration
        config_loaded = self.load_configuration()

        # Check if configuration is needed (skip for certain commands)
        skip_config_commands = ["config", "--help", "-h", "help", "version", "--version"]
        needs_config = True
        if args:
            for skip_cmd in skip_config_commands:
                if skip_cmd in args[0:2]:
                    needs_config = False
                    break

        if needs_config and not config_loaded:
            self.show_configuration_help()
            return 1

        # Show configuration status if loaded
        if config_loaded and not any(x in args for x in ["--quiet", "-q"]):
            console.print(f"[green]✓ Using configuration from {self.config_source}[/green]")

        # Activate virtual environment if available
        self.activate_venv()

        # Run the CLI
        return self.run_cli(args)


def main():
    """Entry point for the wrapper script."""
    wrapper = DomainToolsWrapper()
    sys.exit(wrapper.main())


if __name__ == "__main__":
    main()
