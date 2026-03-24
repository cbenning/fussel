#!/usr/bin/env python3
"""
Serve the generated Fussel gallery site using Python's HTTP server.
Reads the output path from config.yml and starts a local server.
"""

import os
import pathlib
import subprocess
import sys

import yaml


def main():
    # Check if config.yml exists
    config_file = pathlib.Path("config.yml")
    if not config_file.exists():
        print("Error: config.yml not found. Please create it from sample_config.yml first.")
        sys.exit(1)

    # Read config
    try:
        with open(config_file, "r") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading config.yml: {e}")
        sys.exit(1)

    # Get output path
    output_path = cfg.get("gallery", {}).get("output_path", "site/")

    # Handle relative paths
    if not os.path.isabs(output_path):
        output_path = os.path.normpath(os.path.join(config_file.parent, output_path))

    # Check if output directory exists
    if not os.path.exists(output_path):
        print(f"Error: Output directory does not exist: {output_path}")
        print("Please run 'make generate' first to generate the site.")
        sys.exit(1)

    # Check if it's actually a directory
    if not os.path.isdir(output_path):
        print(f"Error: Output path is not a directory: {output_path}")
        sys.exit(1)

    # Start the server
    print(f"Serving site from: {output_path}")
    print("Visit http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server")
    print()

    try:
        subprocess.run(["python3", "-m", "http.server", "--directory", output_path])
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
