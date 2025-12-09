#!/usr/bin/env python3
"""
Shared utility functions for all scripts
This file contains common functions used by multiple scripts
"""

import os
import json
import sys


def load_json(file_path):
    """
    Load a JSON file and return the data

    What this does:
    - Opens the file
    - Parses the JSON
    - Returns the data as a Python dictionary
    - Shows clear error if file not found or invalid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}")
        print(f"  Details: {e}")
        sys.exit(1)


def save_json(file_path, data):
    """
    Save data to a JSON file

    What this does:
    - Converts Python dictionary to JSON text
    - Writes to file with nice formatting (indent=2)
    - Shows error if cannot write
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error: Cannot write to {file_path}")
        print(f"  Details: {e}")
        sys.exit(1)


def write_github_output(key, value):
    """
    Write a variable to GitHub Actions output

    What this does:
    - Makes a variable available to other steps in the workflow
    - The variable can be accessed as: ${{ steps.step_id.outputs.key }}

    Example:
    - write_github_output("region", "eu-frankfurt-1")
    - Later: ${{ steps.backend.outputs.region }}
    """
    github_output_file = os.environ.get("GITHUB_OUTPUT")

    if github_output_file:
        with open(github_output_file, 'a') as f:
            f.write(f"{key}={value}\n")
    else:
        # Running locally, just print for debugging
        print(f"OUTPUT: {key}={value}")


def write_github_env(key, value):
    """
    Write a variable to GitHub Actions environment

    What this does:
    - Makes a variable available as environment variable
    - The variable can be accessed in bash as: $KEY

    Example:
    - write_github_env("DETECTED_REGION", "eu-frankfurt-1")
    - Later in bash: echo $DETECTED_REGION
    """
    github_env_file = os.environ.get("GITHUB_ENV")

    if github_env_file:
        with open(github_env_file, 'a') as f:
            f.write(f"{key}={value}\n")
    else:
        # Running locally, just print for debugging
        print(f"ENV: {key}={value}")


def get_work_temp():
    """
    Get the temporary directory for this workflow

    What this does:
    - Returns the WORK_TEMP environment variable
    - Falls back to /tmp if not set (for local testing)

    Why: Using runner.temp is better than /tmp because:
    - It's isolated per job
    - No permission issues
    - Automatically cleaned up
    """
    return os.environ.get('WORK_TEMP', '/tmp')


def print_section(title):
    """
    Print a section header with nice formatting

    Example output:
    ========================================
    Discovering Backend Configuration
    ========================================
    """
    line = "=" * 50
    print(f"\n{line}")
    print(f"{title}")
    print(f"{line}\n")


def print_error(message):
    """Print error message with consistent format"""
    print(f"❌ Error: {message}")


def print_warning(message):
    """Print warning message with consistent format"""
    print(f"⚠️  Warning: {message}")


def print_success(message):
    """Print success message with consistent format"""
    print(f"✅ {message}")


def print_info(message):
    """Print info message with consistent format"""
    print(f"ℹ️  {message}")
