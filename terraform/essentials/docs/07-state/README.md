# Terraform State and Drift

## Objective (conceptual)

**State** is Terraform's memory of which real-world objects match which configuration addresses. On each plan, Terraform refreshes state from provider APIs and computes a diff. Without state, Terraform would not know whether to create a second VPC or update the existing one.

**Drift** occurs when someone changes infrastructure outside Terraform (console, CLI, another tool). The next `plan` shows differences between configuration, state, and reality. Local state (`terraform.tfstate` in the working directory) is fine for solo labs; teams move to remote backends in the extended track.

**Interactive reference:** [State and Drift](../../html/state.html)

## What state stores

- Resource type, name, and provider-assigned ID
- Last known attribute values (metadata varies by provider)
- Dependencies and lineage for destroy ordering
- Sensitive values unless redacted by provider

Lab 06 creates state with a single `random_pet`—inspect the file after `apply` to see the JSON structure.

## Lab 06: local backend default

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# No backend block means Terraform uses local terraform.tfstate.
resource "random_pet" "first" {
  prefix = "state-lab"
  length = 2
}

output "first_resource" {
  value = random_pet.first.id
}
```

Absence of a `backend` block means **local state** beside your configuration.

## Refresh and plan

- `terraform plan` refreshes by default (unless `-refresh=false`).
- Refresh updates state attributes from the API without applying config changes.
- If the console deleted a resource, plan may show **recreate** to match config.

## Drift scenarios

| Scenario | Plan behavior |
|----------|---------------|
| Tag added in AWS console | Update in place to match `.tf` |
| Instance terminated manually | Create replacement |
| Config changed, cloud unchanged | Update or replace per diff |

## State safety rules

- Do not hand-edit `terraform.tfstate` unless following HashiCorp migration docs.
- Back up state before risky operations (`terraform state mv`, provider upgrades).
- Add `terraform.tfstate` and `*.tfstate.backup` to `.gitignore` for real secrets; labs may commit empty examples only.
- Use `terraform state list` and `terraform state show ADDRESS` for inspection.

## When state moves to remote (preview)

Extended track covers S3 backends, locking with DynamoDB, state keys, and `terraform state pull/push`. Essentials establishes the mental model locally first.

## Isolated lab directories

Each `labs/lab0X-*` folder owns its own state file. Never run commands from the parent `labs/` directory—paths would collide.

## Inspecting state safely

After apply, open `terraform.tfstate` in an editor once to see the JSON shape—then prefer CLI tools for routine work:

```bash
terraform state list
terraform state show random_pet.first
terraform show -json | jq '.values.root_module.resources'
```

Never commit state containing secrets from real environments. Training labs using `random_pet` only are low risk but still teach the habit.

## Replace and taint (concept)

- **Taint** (`terraform taint ADDRESS`) — force recreate on next apply (legacy; prefer `-replace` in Terraform 0.15+).
- **Replace** (`terraform apply -replace=ADDRESS`) — targeted recreation without editing configuration.

Use when a resource is corrupted in the cloud but configuration looks correct.

## State backup before risky changes

```bash
cp terraform.tfstate terraform.tfstate.$(date +%Y%m%d).backup
```

Take a copy before provider major upgrades or manual `state mv` operations.

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab06-local-state
terraform init
terraform apply
terraform state list
terraform state show random_pet.first
terraform plan    # no changes if config matches
terraform destroy
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 06: Local State](../../labmanuals/lab06-local-state.md) | Create and inspect `terraform.tfstate`, refresh behavior |
| [Extended Lab 07: S3 Backend](../../../extended/labmanuals/lab07-s3-backend.md) | Remote state storage (next step for teams) |
