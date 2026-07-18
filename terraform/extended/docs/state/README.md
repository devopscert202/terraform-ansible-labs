# Remote State, Backends, and Locking

## Objective (conceptual)

Team Terraform needs **remote state**: a shared `terraform.tfstate` in durable storage (typically S3) so every engineer and CI job reads the same ID map. **State locking** prevents two applies from corrupting state simultaneously—DynamoDB is the common AWS lock table. **State keys** partition environments and components so `dev/network` never overwrites `prod/compute`.

The mental model: local state is a notebook only you read; remote state is the **system of record** with checkout locks like a library book.

**Interactive reference:** [State (Extended)](../../html/state.html)

## S3 backend skeleton (Lab 07)

```hcl
terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "state_owner" {
  input = "shared-state"
}

output "state_owner" {
  value = terraform_data.state_owner.output
}
```

Backend settings (`bucket`, `key`, `region`, `dynamodb_table`) are supplied at `init` via `-backend-config=backend.hcl`—not hard-coded with secrets in `.tf` files.

## State key layout (Lab 08)

```hcl
variable "environment" {
  type    = string
  default = "dev"
}

locals {
  recommended_key = "extended/${var.environment}/network/terraform.tfstate"
}

output "recommended_state_key" {
  value = local.recommended_key
}
```

Convention example: `extended/dev/network/terraform.tfstate` vs `extended/prod/network/terraform.tfstate`.

## Workspaces vs separate keys

| Approach | Isolation | Best for |
|----------|-----------|----------|
| **Workspace** (`terraform workspace`) | Same backend key prefix, different `terraform.workspace` value | Ephemeral envs, quick sandboxes |
| **Separate state keys** | Distinct `key=` per env/component | Production boundaries, blast radius |

Lab 06 workspaces:

```hcl
locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

output "workspace" {
  value = terraform.workspace
}
```

## Locking flow

1. `terraform apply` acquires lock on DynamoDB table.
2. Second apply blocks with lock error until first completes or lock is force-unlocked (emergency only).
3. Lock releases on success or failure.

Lab 09 exercises lock behavior with a shared backend configuration.

## State migration (concept)

`terraform init -migrate-state` moves local state to remote when you add a `backend` block. Always back up state before migration. Lab 10 walks through pull, push, and verification.

## Remote state consumers

Downstream roots read outputs via `terraform_remote_state` data source (Lab 11)—network team publishes `vpc_id`; app team consumes without duplicating VPC code.

## backend.hcl example pattern

Backend config files stay out of VCS when they name real buckets. Typical `backend.hcl.example` fields:

```hcl
bucket         = "myorg-terraform-state"
key            = "extended/dev/network/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-locks"
encrypt        = true
```

Copy to `backend.hcl`, fill values, then `terraform init -backend-config=backend.hcl`.

## Operational commands (reference)

```bash
cd terraform/extended/labs/lab07-s3-backend
terraform init -backend-config=backend.hcl.example
terraform apply

cd ../lab06-workspaces
terraform workspace list
terraform workspace new dev
terraform apply

cd ../lab09-state-locking
# run two applies in parallel to observe lock

terraform state pull > backup.tfstate
terraform force-unlock <LOCK_ID>   # emergency only — coordinate with team
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 06: Workspaces](../../labmanuals/lab06-workspaces.md) | `terraform workspace`, per-workspace labels |
| [Lab 07: S3 Backend](../../labmanuals/lab07-s3-backend.md) | Configure remote backend with `backend.hcl` |
| [Lab 08: State Keys](../../labmanuals/lab08-state-keys.md) | Naming conventions for environment and component |
| [Lab 09: State Locking](../../labmanuals/lab09-state-locking.md) | DynamoDB lock table behavior |
| [Lab 10: State Migration](../../labmanuals/lab10-state-migration.md) | Migrate local state to remote |
| [Lab 11: Remote State Consumer](../../labmanuals/lab11-remote-state-consumer.md) | Read outputs from another root module |
