# Lab 06 — Workspaces

> **Goal:** Use `terraform.workspace` to derive environment labels and isolate state per workspace.
> **Time:** ~25 min · **Directory:** `terraform/extended/labs/lab06-workspaces/`

## Learning objectives

After completing this lab you will be able to:

- Create, select, and list Terraform workspaces
- Explain state isolation vs variable files
- Use `terraform.workspace` in locals for naming
- Predict output differences across workspaces
- Know when workspaces are insufficient for production isolation

## Architecture

Workspaces partition **state** for the same configuration code — not separate variables files.

```hcl
# main.tf
terraform { required_version = ">= 1.5.0" }

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

resource "terraform_data" "workspace" { input = local.labels }
output "workspace" { value = terraform.workspace }
output "labels" { value = terraform_data.workspace.output }
```

```text
default workspace ──► state A (labels.environment=default)
dev workspace    ──► state B (labels.environment=dev)
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | default apply | baseline labels |
| 2 | new dev | separate state |
| 3 | switch | outputs differ |
| 4 | staging | third workspace |
| 5 | delete | cleanup workspace |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab06-workspaces
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Enter lab directory

Single `main.tf` — no providers.

```bash
cd terraform/extended/labs/lab06-workspaces
cat main.tf
```

**Validate**

```text
Uses `terraform.workspace` in locals.
```

### Step 2 — Initialize

Local backend by default.

```bash
terraform init
```

**Validate**

```text
Initialized successfully.
```

### Step 3 — Show current workspace

Default unless you switched.

```bash
terraform workspace show
```

**Validate**

```text
Reports `default`.
```

### Step 4 — Apply in default

Creates terraform_data with labels.

```bash
terraform apply -auto-approve
```

**Validate**

```text
Outputs `workspace` and `labels` with environment=default.
```

### Step 5 — Create dev workspace

Isolated state file under `terraform.tfstate.d/`.

```bash
terraform workspace new dev
```

**Validate**

```text
Created and switched to `dev`.
```

### Step 6 — Apply in dev

Same code, different state.

```bash
terraform apply -auto-approve
```

**Validate**

```text
labels.environment = dev.
```

### Step 7 — List workspaces

See all environments.

```bash
terraform workspace list
```

**Validate**

```text
Shows default and dev (current marked).
```

### Step 8 — Switch and compare

Return to default state.

```bash
terraform workspace select default
terraform output labels
```

**Validate**

```text
default labels still show environment=default.
```

### Step 9 — State isolation proof

Each workspace has separate state.

```bash
terraform workspace select dev
terraform state list
```

**Validate**

```text
dev state lists `terraform_data.workspace` independently.
```

### Step 10 — Create staging

Practice naming convention.

```bash
terraform workspace new staging
terraform apply -auto-approve
terraform output workspace
```

**Validate**

```text
staging workspace active with matching labels.
```

### Step 11 — Delete workspace

Only after emptying resources.

```bash
terraform workspace select default
terraform workspace delete staging
```

**Validate**

```text
staging removed from list.
```

## Design notes

Workspaces suit small teams with similar configs across environments. They do **not** replace separate AWS accounts, IAM boundaries, or approval gates. Production platforms often prefer directory-per-env or separate state keys (Labs 07–08). `terraform.workspace` in resource names causes replacement if you migrate strategies — plan renames carefully.

## Done when

- [ ] Created dev workspace with distinct outputs
- [ ] Switched workspaces and verified state isolation
- [ ] Explained workspace vs `var.environment` tradeoff

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| Cannot delete workspace | Resources remain | destroy first |
| Wrong output after switch | Forgot to select | `terraform workspace show` |

## Cleanup

```bash
terraform workspace select default
terraform destroy -auto-approve
terraform workspace select dev && terraform destroy -auto-approve
terraform workspace delete dev 2>/dev/null || true
rm -rf .terraform terraform.tfstate* terraform.tfstate.d
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/projects/README.md](../docs/projects/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/projects/README.md](../docs/projects/README.md) · Next: [Lab 07 — S3 backend](lab07-s3-backend.md)*

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
