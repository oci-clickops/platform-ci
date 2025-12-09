# Platform CI

Shared GitOps workflows for multi-cloud infrastructure (OCI + Azure).

## Quick Start

```yaml
# In your project repo
jobs:
  terraform:
    uses: oci-clickops/platform-ci-v2/.github/workflows/terraform-shared.yaml@main
    with:
      mode: ${{ github.event_name == 'pull_request' && 'pr' || 'apply' }}
      cloud: oci
      orchestrator_repo: oci-clickops/clickops-terraform-oci-modules-orchestrator
      bucket_name: clickops-common-bucket
```

## Structure

```
.github/workflows/
├── terraform-shared.yaml    # Terraform plan/apply
└── ansible-shared.yaml      # Ansible check/execute

scripts_python/
├── utils.py                 # OCI bucket utilities
└── ansible_inventory.py     # Dynamic inventory from Terraform state

ansible/
├── ansible.cfg
├── requirements.yml
└── playbooks/master.yml     # ADB lifecycle operations

operations-catalog/          # APEX UI catalog
├── adb-lifecycle.json
└── deploy-agent.json
```

## Workflows

| Workflow | Inputs | Purpose |
|----------|--------|---------|
| `terraform-shared` | mode, cloud, orchestrator_repo, bucket_name | Terraform GitOps |
| `ansible-shared` | mode, cloud, operation_file, bucket_name | Ansible Day-2 ops |

## Authentication

- **OCI**: Instance Principal (self-hosted runners)
- **Azure**: Service Principal (env vars)

## Requirements

- Self-hosted runner with OCI CLI
- Terraform >= 1.12.0
- Python 3.11+
