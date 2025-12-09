# Platform CI

Reusable GitHub Actions workflows for multi-cloud GitOps (Terraform + Ansible).

## Overview

This repository provides centralized CI/CD workflows for:

- **Terraform**: Infrastructure provisioning (OCI, Azure)
- **Ansible**: Day-2 operations and lifecycle management (ADB)

## Structure

```
.github/
├── workflows/
│   ├── terraform-shared.yaml      # Terraform workflow (Plan & Apply)
│   └── ansible-shared.yaml        # Ansible workflow (Check & Execute)
├── actions/
│   ├── terraform-workflow/        # Terraform composite action
│   └── ansible-workflow/          # Ansible composite action  
├── scripts_python/                # Python scripts (10 total)
│   ├── discover.py               # Discovery (terraform|ansible)
│   ├── terraform_setup.py        # Terraform backend setup
│   ├── ansible_state.py          # Ansible state (load|update)
│   ├── ansible_generate_inventory.py  # Dynamic inventory
│   ├── ansible_precheck.py       # Pre-checks
│   └── ...                       # Utility modules
└── ansible/
    ├── playbooks/master.yml      # Tag-routed playbook
    └── roles/adb-lifecycle/      # ADB start/stop operations
```

## Workflows

### Terraform Workflow

**Purpose**: Plan and apply infrastructure changes

**Usage** (in manifest repo):

```yaml
name: OCI Terraform GitOps
on:
  pull_request:
    paths: ['oci/**']
  push:
    branches: [main]
    paths: ['oci/**']

jobs:
  terraform:
    uses: oci-clickops/platform-ci/.github/workflows/terraform-shared.yaml@main
    with:
      cloud: oci
      orchestrator_repo: oci-clickops/clickops-terraform-oci-modules-orchestrator
      runner: self-hosted, oci
```

### Ansible Workflow

**Purpose**: Execute day-2 operations on infrastructure

**Usage** (in manifest repo):

```yaml
name: OCI Ansible Operations
on:
  workflow_dispatch:
    inputs:
      operation_file:
        description: 'Operation file path'
        required: true
      mode:
        description: 'Execution mode'
        required: true
        type: choice
        options: [check, execute]

jobs:
  ansible:
    uses: oci-clickops/platform-ci/.github/workflows/ansible-shared.yaml@main
    with:
      operation-file: ${{ inputs.operation_file }}
      mode: ${{ inputs.mode }}
      cloud: oci
```

## Key Features

- 🔄 **100% Procedural** - No OOP, simple Python functions
- 🚀 **OCI CLI-based** - No Python SDK dependencies
- 📦 **Consolidated Scripts** - 10 scripts total (down from 18)
- 🎯 **MVP Focused** - ADB lifecycle operations only
- 👨‍🎓 **Junior-Friendly** - Clear, simple, documented code

## Scripts

### Core Utilities (5)

- `common.py` - Shared functions (JSON, logging, GitHub outputs)
- `config.py` - Constants and paths
- `oci_cli_utils.py` - OCI CLI wrappers (subprocess-based)
- `state_functions.py` - Ansible state management
- `discovery_functions.py` - Discovery functions

### Executables (5)

- `discover.py` - Backend/operation discovery (terraform|ansible)
- `terraform_setup.py` - Terraform backend configuration
- `ansible_state.py` - Ansible state management (load|update)
- `ansible_generate_inventory.py` - Dynamic inventory from Terraform state
- `ansible_precheck.py` - Pre-execution validation

## Authentication

- **OCI**: Instance Principal (automatic on self-hosted runners)
- **Azure**: Service Principal (configured in GitHub secrets)

## State Management

- **Terraform State**: OCI Object Storage (`{bucket}/{cloud}/{region}/terraform.tfstate`)
- **Ansible State**: OCI Object Storage (`{bucket}/ansible/{cloud}/{region}/ansible-state-{operation}.json`)

## Requirements

### Runner Setup

- OCI CLI configured with Instance Principal
- Terraform >= 1.12.0
- Ansible >= 2.15
- Python 3.8+

### Collections

- `oracle.oci` (for Ansible OCI operations)

## License

MIT
