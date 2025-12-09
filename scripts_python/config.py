#!/usr/bin/env python3
"""
Configuration constants for all scripts
This file contains paths, file names, and other constants
"""

import os

# Directory names
ORCHESTRATOR_DIR = "ORCH"
PLAYBOOKS_DIR = "ansible/playbooks"
ROLES_DIR = "ansible/roles"

# File names
TERRAFORM_STATE_FILE = "terraform.tfstate"
PROVIDERS_FILE = "providers.tf"
INVENTORY_FILE = "inventory.json"
ANSIBLE_STATE_FILE = "ansible-state.json"


def get_work_temp():
    """
    Get the work temp directory from environment
    Falls back to /tmp if not set (for local testing)
    """
    return os.environ.get('WORK_TEMP', '/tmp')


def get_inventory_path():
    """Get the full path to the inventory file"""
    return os.path.join(get_work_temp(), INVENTORY_FILE)


def get_ansible_state_path():
    """Get the full path to the ansible state file"""
    return os.path.join(get_work_temp(), ANSIBLE_STATE_FILE)


def get_ansible_log_path(mode):
    """
    Get the full path to the ansible log file
    mode: 'check' or 'execute'
    """
    return os.path.join(get_work_temp(), f"ansible-{mode}.log")


def get_terraform_state_key(bucket, config_path):
    """
    Build the object key for Terraform state file

    Format: {bucket}/{config_path}/terraform.tfstate
    Example: clickops-common-bucket/oci/eu-frankfurt-1/terraform.tfstate

    Note: The bucket name appears in the key as organizational prefix
    """
    return f"{bucket}/{config_path}/{TERRAFORM_STATE_FILE}"


def get_ansible_state_key(bucket, config_path, operation_type):
    """
    Build the object key for Ansible state file

    Format: {bucket}/ansible/{config_path}/ansible-state-{operation}.json
    Example: clickops-common-bucket/ansible/oci/eu-frankfurt-1/ansible-state-adb-lifecycle.json

    Note: Ansible state is in a separate 'ansible/' subdirectory
          to avoid conflicts with Terraform state
    """
    return f"{bucket}/ansible/{config_path}/ansible-state-{operation_type}.json"


def get_ansible_log_file(mode):
    """
    Get the log file name for Ansible execution

    mode: 'check' or 'execute'
    Returns: 'ansible-check.log' or 'ansible-execute.log'
    """
    return f"ansible-{mode}.log"


# Ansible versions
ANSIBLE_VERSION = "2.16.0"
OCI_COLLECTION_VERSION = "5.5.0"

# Terraform version
TERRAFORM_VERSION = "1.12.1"
