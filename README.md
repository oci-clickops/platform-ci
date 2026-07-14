# Platform CI

Shared GitOps workflows for multi-cloud infrastructure (OCI, Azure, and GCP).

## Quick Start

```yaml
# In your project repo
jobs:
  terraform:
    uses: oci-clickops/platform-ci/.github/workflows/terraform-shared.yaml@main
    secrets: inherit
    with:
      mode: ${{ github.event_name == 'pull_request' && 'pr' || 'apply' }}
      cloud: oci
      region: eu-frankfurt-1
      orchestrator_repo: oci-clickops/clickops-terraform-oci-modules-orchestrator
      bucket_name: clickops-common-bucket
      # runner_labels: '["self-hosted","oci"]'
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
└── playbooks/
    ├── master.yml           # Operation router (tags)
    ├── common/send-notification.yml
    └── operations/adb-lifecycle.yml
```

## Workflows

| Workflow | Inputs | Purpose |
|----------|--------|---------|
| `terraform-shared` | mode, cloud, orchestrator_repo, bucket_name | Terraform GitOps |
| `ansible-shared` | mode, cloud, operation_file, bucket_name | Ansible Day-2 ops |

## Caller Repo Layout (Expected)

These workflows are designed to be called from a “manifest” repo that contains per-cloud/per-region config.

```
<your-repo>/
├── oci/
│   └── eu-frankfurt-1/
│       ├── *.json                 # Terraform var-files (JSON)
│       └── lifecycle_operations/
│           └── adb-lifecycle.json # Operation manifest(s)
├── azure/
│   └── westeurope/
│       └── *.json                 # Terraform var-files (JSON)
└── gcp/
    └── europe-west2/
        └── *.json                 # Terraform var-files (JSON)
```

## Terraform Workflow (`terraform-shared.yaml`)

**Inputs**

- `mode`: `pr` (plan + PR comment) or `apply` (apply)
- `cloud`: `oci`, `azure`, or `gcp`
- `region`: (Optional) Config folder name (e.g., `eu-frankfurt-1`, `westeurope`, `europe-west2`). **If omitted**, the workflow automatically detects it by checking which files changed in the `{cloud}/` directory.
- `orchestrator_repo`: repo containing the Terraform modules/orchestrator (checked out into `ORCH/`)
- `bucket_name`: OCI Object Storage bucket name used for the Terraform backend
- `runner_labels` (optional): JSON array for `runs-on` (default: `["self-hosted","oci"]`)

**Config resolution**

The workflow determines the configuration directory in this order:

1. Input `region` (if provided)
2. **Auto-detection**: Checks `git diff` for changes in `${cloud}/<region>/...`
3. Runner `REGION` env var

It then resolves to `${cloud}/${region}` (e.g., `oci/eu-frankfurt-1` or `gcp/europe-west2`) and passes all `*.json` files found there to Terraform.

Terraform does not deep-merge repeated root variables across `-var-file` inputs. Keep aggregated roots in one manifest per region, for example OCI project NSGs in `oci/<region>/network/project-nsgs.json` and Google ADB-S entries in `gcp/<region>/workloads/adb.json`.

In `apply` mode, the workflow first creates `tfplan.binary` from the merged commit and then applies that exact saved plan. It does not pass the variable files to `terraform apply`, because doing so would generate a second implicit plan that could differ from the plan shown earlier in the job.

**Runtime secret placeholder substitution**

Before Terraform runs, the workflow copies JSON var-files to `${{ runner.temp }}/terraform-var-files`, excludes `lifecycle_operations/` manifests, and replaces double-underscore placeholders from environment values or inherited GitHub Actions secrets. The checked-out manifest repository is not modified.

For OCI ADB manifests, use one secret placeholder per database when passwords should differ, for example `__ADB_PROD_PROJ1_01_ADMIN_PASSWORD__` in Git and a project-repository secret named `ADB_PROD_PROJ1_01_ADMIN_PASSWORD`. Caller workflows must include `secrets: inherit` so the reusable workflow can read the secret. The workflow fails before planning if any unresolved `__PLACEHOLDER__` remains in Terraform var-files.

Changing a GitHub secret does not rotate an existing OCI ADB password because the ADB module ignores `admin_password` drift after creation. Password rotation should be handled as an explicit Day 2 operation.

**Terraform state object name**

The backend `key` (and the Ansible inventory downloader) uses:

`<bucket_name>/<github.repository>/<cloud>/<region>/terraform.tfstate`

## Ansible Workflow (`ansible-shared.yaml`)

Runs Day-2 operations using Ansible, driven by a JSON “operation manifest”.

**Inputs**

- `mode`: `check` or `execute`
- `cloud`: currently only `oci` is supported end-to-end (inventory generation rejects `azure`)
- `operation_file` (optional): path to the operation JSON; if omitted, it is auto-detected from the git diff
- `bucket_name`: OCI Object Storage bucket used to download Terraform state
- `runner_labels` (optional): JSON array for `runs-on` (default: `["self-hosted","oci"]`)

**Operation auto-detection**

When `operation_file` is empty, the workflow picks the first changed file matching:

- path contains `${cloud}`
- path contains `lifecycle_operations`
- filename ends with `.json`

Recommended location: `${cloud}/${region}/lifecycle_operations/<operation>.json`.

**Operation JSON format**

`operation_type` must match the Ansible tag in `ansible/playbooks/master.yml` (e.g., `adb-lifecycle`).

```json
{
  "operation_type": "adb-lifecycle",
  "targets": [
    { "display_name": "my-adb", "action": "stop", "wait_for_state": true, "timeout_minutes": 30 }
  ]
}
```

Targets are matched against ADB `display_name` values found in Terraform state (`oci_database_autonomous_database` resources).

For `deploy-agent`, targets are matched against compute instance `display_name` values found in Terraform state (`oci_core_instance` resources). The generated inventory connects over SSH to the instance private IP using `ansible_user=opc` and `ansible_ssh_private_key_file=/home/opc/.ssh/oci_vm_key` by default. Override these on the self-hosted runner with `COMPUTE_ANSIBLE_USER` and `COMPUTE_SSH_PRIVATE_KEY_FILE` if a project image uses a different OS user or key path.

## Authentication

- **OCI**: Instance Principal (self-hosted runners)
- **Azure**: Service Principal (env vars)
- **Google**: Google provider credentials through `GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default Credentials on the runner

### OCI Project IAM Boundary

Project repositories should not create OCI IAM foundation resources. Project compartments, groups, and IAM policies are created by `oci-clickops-lz/op04_manage_project` before handoff. Project repos record handoff references in `enviroment_information.md` and consume those values in workload and NSG manifests.

Do not add `oci-credentials.tfvars.json`, `project-iam.json`, or OCI compartment/group/policy manifests to project repositories. For ADB, VM, storage, and project NSG provisioning, Instance Principal authentication on the runner is sufficient.

## Requirements

- Linux self-hosted runner (bash + GNU utils)
- Terraform >= 1.12.0
- Python 3.11+ (Ansible workflow installs Ansible via pip)
- Azure CLI available on the runner when `cloud: azure` is used (`az login` is invoked)
- Google provider credentials available on the runner when `cloud: gcp` is used
- OCI Instance Principal available on the runner for OCI Object Storage state access

## Regions

- `STATE_REGION` is the **OCI region where the Terraform state bucket lives** (used by OCI, Azure, and Google jobs because the backend is OCI Object Storage).
- Config selection uses `oci/<region>/...`, `azure/<region>/...`, or `gcp/<region>/...` and is controlled by path auto-detection, the workflow input `region`, or runner env `REGION`. `STATE_REGION` is used as a legacy OCI-only config-region fallback.

> [!NOTE]
> **Future Improvement:** Currently `STATE_REGION` must be configured on the runner. For OCI-only single-region setups where the state bucket lives in the same region as resources, this could be simplified by deriving `STATE_REGION` from the OCI config region.

## Environment Variables [WORKAROUND]

These must be configured on the self-hosted runner:

| Variable | Description | Cloud | Sensitive |
|----------|-------------|-------|-----------|
| `STATE_NAMESPACE` | OCI Object Storage namespace | OCI | No |
| `STATE_REGION` | OCI region where the state bucket lives (required) | OCI/Azure/GCP | No |
| `REGION` | Config region folder name (used when path auto-detection or workflow input `region` is not available) | OCI/Azure/GCP | No |
| `OCI_CLI_AUTH` | Set to `instance_principal` (needed for `oci os object get` in inventory generation) | OCI | No |
| `COMPUTE_ANSIBLE_USER` | Optional SSH user for compute Day 2 operations; defaults to `opc` | OCI | No |
| `COMPUTE_SSH_PRIVATE_KEY_FILE` | Optional private key path for compute Day 2 operations; defaults to `/home/opc/.ssh/oci_vm_key` | OCI | Yes |
| `ARM_CLIENT_ID` | Service Principal client ID | Azure | Yes |
| `ARM_CLIENT_SECRET` | Service Principal secret | Azure | Yes |
| `ARM_TENANT_ID` | Azure tenant ID | Azure | No |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID | Azure | No |
| `GOOGLE_CREDENTIALS` | Google service account JSON or workload identity credential JSON | Google | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to a Google ADC credentials file | Google | Yes |

GitHub Actions project-repository secrets:

| Secret | Description | Cloud |
|--------|-------------|-------|
| `<PLACEHOLDER_NAME>` | Replaces `__<PLACEHOLDER_NAME>__` in prepared Terraform var-files, for example `ADB_PROD_PROJ1_01_ADMIN_PASSWORD` | OCI |

### Runner Configuration

Configure variables in the Systemd service file (`/etc/systemd/system/actions.runner...service`):

```ini
[Service]
# OCI
Environment="OCI_CLI_AUTH=instance_principal"
Environment="STATE_NAMESPACE=..."
Environment="STATE_REGION=eu-frankfurt-1"
Environment="REGION=eu-frankfurt-1"  # optional if workflows pass `region`

# Azure
Environment="ARM_SUBSCRIPTION_ID=..."
Environment="ARM_CLIENT_ID=..."
Environment="ARM_CLIENT_SECRET=..."
Environment="ARM_TENANT_ID=..."
```

Then reload: `systemctl daemon-reload && systemctl restart actions-runner...`

> **Note**: This is more secure than a `.env` file as it is owned by root.

## Scalability

Designed for multiple projects without bottlenecks:

- **Concurrency**: Each project has its own queue (scoped by `github.repository`)
  - Project A running Terraform does NOT block Project B
  - Only same-project operations serialize (prevents state conflicts)
  
- **Runner Capacity**: Add more runners to handle concurrent load
