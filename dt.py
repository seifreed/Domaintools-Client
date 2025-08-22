#!/usr/bin/env python3
"""DomainTools CLI Wrapper Script."""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Import the CLI after path is set
from domaintools_client.cli.main import cli  # noqa: E402

if __name__ == "__main__":
    # Set up default environment if not already set
    env_file = project_dir / ".env"
    if env_file.exists() and not os.getenv("DOMAINTOOLS_API_KEY"):
        from dotenv import load_dotenv

        load_dotenv(env_file)

    # Check for config file in project root
    config_files = ["config.yaml", "config.yml", "domaintools.yaml", "domaintools.yml"]
    config_file = None
    for cf in config_files:
        cf_path = project_dir / cf
        if cf_path.exists():
            config_file = str(cf_path)
            break

    # Run the CLI
    try:
        cli(standalone_mode=False, obj={})
    except Exception as e:
        if "--debug" in sys.argv or os.getenv("DEBUG"):
            raise
        else:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
