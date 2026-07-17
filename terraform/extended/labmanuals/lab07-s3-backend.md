# Lab 07 — S3 backend

> **Goal:** Initialize encrypted shared state in a pre-existing S3 bucket with lockfile support.
> **Time:** ~40 min · **Directory:** `terraform/extended/labs/lab07-s3-backend/`

## Learning objectives

After completing this lab you will be able to:

- Configure S3 backend via external `backend.hcl`
- Use `terraform init -backend=false` for safe syntax validation
- Enable `use_lockfile` for concurrent write protection
- Identify `terraform_data.state_owner` as state ownership marker
- Explain why backend settings cannot use input variables

## Architecture

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "state_owner" { input = "shared-state" }
output "state_owner" { value = terraform_data.state_owner.output }
```

**Backend config example** (`backend.hcl.example`):

```hcl
bucket       = "replace-with-unique-state-bucket"
key          = "extended/lab07/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | -backend=false | Safe validate |
| 2 | backend.hcl | Remote config |
| 3 | init | S3 connected |
| 4 | apply | Remote state write |
| 5 | S3 ls | Object exists |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab07-s3-backend
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Navigate to lab directory

State labs use S3 backend block — prepare bucket first.

```bash
cd terraform/extended/labs/lab07-s3-backend
ls -la
```

**Validate**

```text
main.tf and backend.hcl.example present.
```

### Step 2 — Read backend block

Empty `backend "s3" {}` — values come from backend config file.

```bash
grep -A2 'backend' main.tf
```

**Validate**

```text
`backend "s3" {}` with no inline attributes.
```

### Step 3 — Local validation pass

Syntax check without touching remote state.

```bash
terraform init -backend=false
terraform validate
```

**Validate**

```text
Valid configuration without backend connection.
```

### Step 4 — Review backend.hcl.example

Copy and edit before real init.

```bash
cat backend.hcl.example
cp backend.hcl.example backend.hcl
# Edit bucket, key, region
```

**Validate**

```text
backend.hcl customized with your training bucket.
```

### Step 5 — Verify S3 bucket exists

Bucket must pre-exist; Terraform does not create it here.

```bash
aws s3 ls s3://YOUR-STATE-BUCKET --profile $AWS_PROFILE
```

**Validate**

```text
Bucket listing succeeds or empty bucket confirmed.
```

### Step 6 — Initialize remote backend

Connects to S3; use_lockfile enables native locking.

```bash
terraform init -backend-config=backend.hcl
```

**Validate**

```text
Backend configured; state migrated or created.
```

### Step 7 — Plan

Review terraform_data resource for this lab's teaching point.

```bash
terraform plan
```

**Validate**

```text
Plan matches lab intent — typically one terraform_data.
```

### Step 8 — Apply

Writes state remotely.

```bash
terraform apply -auto-approve
```

**Validate**

```text
Apply complete with lab-specific output.
```

### Step 9 — Confirm remote state

Object appears at configured key.

```bash
aws s3 ls s3://YOUR-STATE-BUCKET/extended/ --recursive | head
```

**Validate**

```text
terraform.tfstate object visible in bucket.
```

### Step 10 — State list locally

CLI still works against remote backend.

```bash
terraform state list
```

**Validate**

```text
terraform_data address listed.
```

### Step 11 — Inspect state_owner output

Marker for shared-state exercises.

```bash
terraform output state_owner
```

**Validate**

```text
Value is `shared-state`.
```

### Step 12 — Second init

Re-init should be idempotent.

```bash
terraform init -backend-config=backend.hcl
```

**Validate**

```text
Terraform has been successfully initialized.
```

## Design notes

Remote state is operational data — encrypt at rest, restrict IAM to state prefixes, enable versioning for recovery. The empty `backend "s3" {}` block forces backend config into reviewed files rather than variables. `use_lockfile = true` (Terraform 1.5+) replaces DynamoDB for many teams. Always run `init -backend=false` first in CI to validate HCL without credentials.

## Done when

- [ ] Remote backend initialized with encryption and lockfile
- [ ] Applied with state stored in S3
- [ ] Explained why backend cannot use variables

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| Backend init AccessDenied | IAM/bucket policy | Fix prefix permissions |
| Region mismatch | backend.hcl wrong region | Match bucket region |
| Lock file errors | Concurrent apply | Wait or investigate holder |

## Cleanup

```bash
terraform destroy -auto-approve
rm -f backend.hcl
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
*Deep dive: [docs/state/README.md](../docs/state/README.md) · Next: [Lab 08 — State keys](lab08-state-keys.md)*

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
