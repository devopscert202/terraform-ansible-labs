# Lab 11 — Remote state consumer

> **Goal:** Read upstream stack outputs using `data.terraform_remote_state` and a configurable state path.
> **Time:** ~35 min · **Directory:** `terraform/extended/labs/lab11-remote-state-consumer/`

## Learning objectives

After completing this lab you will be able to:

- Configure `terraform_remote_state` with local backend
- Set `network_state_path` to producer state file
- Apply producer before consumer
- Treat outputs as versioned contracts
- Contrast local path vs S3 backend for production

## Architecture

Consumer stack reads producer outputs through `data.terraform_remote_state` with **local** backend pointing at producer's state file path.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
}

variable "network_state_path" {
  type    = string
  default = "../lab08-state-keys/terraform.tfstate"
}

data "terraform_remote_state" "network" {
  backend = "local"
  config = {
    path = var.network_state_path
  }
}

output "upstream_outputs" {
  value = data.terraform_remote_state.network.outputs
}
```

```text
lab08 (producer) ──state file──► data.terraform_remote_state.network
                                      └──► output upstream_outputs
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | Producer apply | State with outputs |
| 2 | Consumer init | Data source ready |
| 3 | upstream_outputs | Producer data visible |
| 4 | Producer change | Consumer plan updates |
| 5 | Custom path | Variable override |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab11-remote-state-consumer
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Apply producer first

Lab 08 (or 10) must have applied state with outputs.

```bash
cd ../lab08-state-keys
terraform output recommended_state_key 2>/dev/null || true
```

**Validate**

```text
Producer state exists or you note path to substitute.
```

### Step 2 — Enter consumer directory

No managed resources — data source only.

```bash
cd ../lab11-remote-state-consumer
cat main.tf
```

**Validate**

```text
data block uses local backend.
```

### Step 3 — Review network_state_path

Default relative path to lab08 state.

```bash
grep -A4 'network_state_path' main.tf
```

**Validate**

```text
Default `../lab08-state-keys/terraform.tfstate`.
```

### Step 4 — Initialize consumer

No S3 backend in consumer for this exercise.

```bash
terraform init
terraform validate
```

**Validate**

```text
Valid consumer configuration.
```

### Step 5 — Plan consumer

Reads remote state at plan time.

```bash
terraform plan
```

**Validate**

```text
Plan may show output changes based on upstream.
```

### Step 6 — Apply consumer

Stores data source result in local state.

```bash
terraform apply -auto-approve
```

**Validate**

```text
upstream_outputs populated.
```

### Step 7 — Inspect outputs

See producer outputs reflected.

```bash
terraform output upstream_outputs
```

**Validate**

```text
Contains producer output map.
```

### Step 8 — Change producer

Re-apply producer with different environment.

```bash
cd ../lab08-state-keys
terraform apply -auto-approve -var='environment=qa'
```

**Validate**

```text
Producer output changes.
```

### Step 9 — Re-plan consumer

Downstream detects upstream drift.

```bash
cd ../lab11-remote-state-consumer
terraform plan
```

**Validate**

```text
Output change if producer outputs changed.
```

### Step 10 — Custom state path

Override via variable.

```bash
terraform plan -var='network_state_path=../lab10-state-migration/terraform.tfstate'
```

**Validate**

```text
Plan succeeds if alternate state file exists.
```

### Step 11 — Document contract

List which producer outputs consumers need.

```bash
terraform output -json upstream_outputs | jq .
```

**Validate**

```text
JSON documents interface for hypothetical app stack.
```

## Design notes

Consumers depend on producer output **names** — renames break downstream plans. Export minimal outputs (`vpc_id`, subnet ids) not entire resource objects. For production, switch data source to S3 backend matching producer key. Do not use remote state as a discovery API for unrelated resources.

## Done when

- [ ] Applied producer and consumer successfully
- [ ] Read upstream_outputs
- [ ] Explained output contract risks

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| Empty upstream_outputs | Producer not applied | Apply lab08 first |
| State file not found | Wrong network_state_path | Fix relative path |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/state/README.md](../docs/state/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/state/README.md](../docs/state/README.md) · Next: [Lab 12 — Collections](lab12-collections.md)*

## Reference — command cheat sheet


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |

## Reference — S3 backend checklist


| Item | Action |
|------|--------|
| Bucket exists | Created by platform team, not this lab |
| Versioning | Enabled for rollback |
| Encryption | `encrypt = true` in backend.hcl |
| Locking | `use_lockfile = true` for Terraform 1.5+ |
| IAM | Role can `s3:GetObject`, `PutObject`, `DeleteObject` on prefix |
| Key | Matches `extended/<env>/<component>/terraform.tfstate` pattern |

## Reference — migration safety


Never migrate state during an active incident or concurrent apply.

1. Announce maintenance window to team
2. Copy `terraform.tfstate` to dated backup
3. Run `terraform state list` and archive output
4. Execute `terraform init -migrate-state`
5. Run `terraform plan` — expect **no changes**
6. If plan shows recreation, **stop** and restore backup

## Reference — remote state consumer


Producer stack exports:

```hcl
output "vpc_id" { value = aws_vpc.this.id }
```

Consumer stack reads:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "state-bucket"
    key    = "extended/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Treat output names as API contracts.

## Reference — command cheat sheet (continued 2)


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions (continued 2)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts (continued 2)


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab (continued 2)


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links (continued 2)


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |

## Reference — S3 backend checklist (continued 2)


| Item | Action |
|------|--------|
| Bucket exists | Created by platform team, not this lab |
| Versioning | Enabled for rollback |
| Encryption | `encrypt = true` in backend.hcl |
| Locking | `use_lockfile = true` for Terraform 1.5+ |
| IAM | Role can `s3:GetObject`, `PutObject`, `DeleteObject` on prefix |
| Key | Matches `extended/<env>/<component>/terraform.tfstate` pattern |

## Reference — migration safety (continued 2)


Never migrate state during an active incident or concurrent apply.

1. Announce maintenance window to team
2. Copy `terraform.tfstate` to dated backup
3. Run `terraform state list` and archive output
4. Execute `terraform init -migrate-state`
5. Run `terraform plan` — expect **no changes**
6. If plan shows recreation, **stop** and restore backup

## Reference — remote state consumer (continued 2)


Producer stack exports:

```hcl
output "vpc_id" { value = aws_vpc.this.id }
```

Consumer stack reads:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "state-bucket"
    key    = "extended/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Treat output names as API contracts.

## Reference — command cheat sheet (continued 3)


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |
