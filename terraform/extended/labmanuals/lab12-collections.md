# Lab 12 — Collections

> **Goal:** Model infrastructure with maps, sets, `for_each`, and `sort` for deterministic outputs.
> **Time:** ~30 min · **Directory:** `terraform/extended/labs/lab12-collections/`

## Learning objectives

After completing this lab you will be able to:

- Define `map(object(...))` variables for structured data
- Use `for_each` with stable string keys
- Convert `set` to sorted list with `sort(tolist(...))`
- Predict replacement when map keys change
- Read for_each resource addresses in state

## Architecture

Maps and sets drive `for_each` and ordering functions.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
}

variable "availability_zones" {
  type    = set(string)
  default = ["us-east-1a", "us-east-1b"]
}
variable "subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}

resource "terraform_data" "subnet" {
  for_each = var.subnets
  input    = { name = each.key, cidr = each.value.cidr, az = each.value.az }
}

output "zones" { value = sort(tolist(var.availability_zones)) }
output "subnet_ids" { value = { for name, item in terraform_data.subnet : name => item.id } }
```

```text
var.subnets (map) ──for_each──► terraform_data.subnet[*]
var.availability_zones (set) ──sort──► output zones
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | Map variable | subnets structure |
| 2 | for_each | Per-key instances |
| 3 | sort output | Ordered zones |
| 4 | Add key | Third subnet |
| 5 | State list | Bracket addresses |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab12-collections
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Review subnet map

Object-typed map variable.

```bash
cd terraform/extended/labs/lab12-collections
grep -A8 'variable "subnets"' main.tf
```

**Validate**

```text
Keys `app_a`, `app_b` with cidr and az.
```

### Step 2 — Review for_each resource

One instance per map key.

```bash
grep -A5 'for_each = var.subnets' main.tf
```

**Validate**

```text
each.key and each.value used.
```

### Step 3 — Initialize and validate

Pure Terraform — no cloud.

```bash
terraform init
terraform validate
```

**Validate**

```text
Valid.
```

### Step 4 — Plan

Two terraform_data instances expected.

```bash
terraform plan
```

**Validate**

```text
Shows `app_a` and `app_b` instances.
```

### Step 5 — Apply

Materialize collection resources.

```bash
terraform apply -auto-approve
```

**Validate**

```text
subnet_ids output map populated.
```

### Step 6 — Inspect zones output

set converted to sorted list.

```bash
terraform output zones
```

**Validate**

```text
Sorted AZ list.
```

### Step 7 — Add third subnet via -var

Extend map at apply time.

```bash
terraform apply -auto-approve -var='subnets={app_a={cidr="10.0.1.0/24",az="us-east-1a"},app_b={cidr="10.0.2.0/24",az="us-east-1b"},app_c={cidr="10.0.3.0/24",az="us-east-1c"}}'
```

**Validate**

```text
Third instance created — keys are stable addresses.
```

### Step 8 — Console practice

Evaluate sort on sets.

```bash
terraform console
```

**Validate**

```text
Type `sort(tolist(var.availability_zones))` — matches output.
```

### Step 9 — Key rename warning

Renaming map key destroys/recreates instance.

```bash
# Change app_a to app_alpha in tfvars mentally
terraform plan -var='...'
```

**Validate**

```text
Plan shows destroy/create on key rename.
```

### Step 10 — State addresses

for_each uses map key in address.

```bash
terraform state list
```

**Validate**

```text
Addresses like `terraform_data.subnet["app_a"]`.
```

## Design notes

Prefer `for_each` over `count` when instances have meaningful names — reordering lists under `count` shifts indices and forces recreation. Sort sets before display to reduce noisy plan diffs. Validate map shapes with variable `type` constraints early.

## Done when

- [ ] Applied for_each subnets
- [ ] Demonstrated sorted zones output
- [ ] Explained key rename impact

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| `Invalid for_each argument` | Wrong type | Ensure map or set of strings |
| Unexpected destroy | Renamed key | Expected for_each behavior |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/functions/README.md](../docs/functions/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/functions/README.md](../docs/functions/README.md) · Next: [Lab 13 — Functions](lab13-functions.md)*

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
