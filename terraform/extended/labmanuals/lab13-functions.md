# Lab 13 — Functions

> **Goal:** Transform strings, collections, and CIDRs using Terraform's pure functions at plan time.
> **Time:** ~30 min · **Directory:** `terraform/extended/labs/lab13-functions/`

## Learning objectives

After completing this lab you will be able to:

- Chain `lower` and `replace` for DNS-safe slugs
- Deduplicate lists with `toset` and `sort`
- Allocate subnets with `cidrsubnet`
- Serialize structures via `jsonencode`
- Use `terraform console` to debug expressions

## Architecture

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
}

variable "application" {
  type    = string
  default = "payments api"
}
variable "cidrs" {
  type    = list(string)
  default = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}

locals {
  slug          = lower(replace(var.application, " ", "-"))
  unique_cidrs  = sort(tolist(toset(var.cidrs)))
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)
  configuration = jsonencode({ name = local.slug, cidrs = local.unique_cidrs })
}
resource "terraform_data" "functions" { input = local.configuration }
output "results" { value = { slug = local.slug, cidrs = local.unique_cidrs, subnet = local.subnet_prefix, json = terraform_data.functions.output } }
```

```text
var.application ──► lower(replace(...)) ──► slug
var.cidrs ──► toset ──► sort ──► unique_cidrs
cidrsubnet("10.20.0.0/16", 8, 12) ──► subnet_prefix
locals ──► jsonencode ──► terraform_data.functions
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | locals | Four patterns |
| 2 | console slug | payments-api |
| 3 | cidrsubnet | 10.20.12.0/24 |
| 4 | dedupe | Unique cidrs |
| 5 | jsonencode | JSON output |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab13-functions
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Read locals block

Four function patterns in one place.

```bash
cd terraform/extended/labs/lab13-functions
sed -n '/^locals/,/^}/p' main.tf
```

**Validate**

```text
slug, unique_cidrs, subnet_prefix, configuration visible.
```

### Step 2 — Initialize

No providers.

```bash
terraform init
terraform validate
```

**Validate**

```text
Valid.
```

### Step 3 — Apply defaults

See computed results.

```bash
terraform apply -auto-approve
```

**Validate**

```text
results output with slug and cidrs.
```

### Step 4 — Console: slug

Interactive function testing.

```bash
terraform console
```

**Validate**

```text
`lower(replace("payments api", " ", "-"))` → payments-api.
```

### Step 5 — Console: cidrsubnet

Plan subnet allocations.

```bash
terraform console
```

**Validate**

```text
`cidrsubnet("10.20.0.0/16", 8, 12)` → 10.20.12.0/24.
```

### Step 6 — Console: dedupe

toset removes duplicates.

```bash
terraform console
```

**Validate**

```text
`sort(tolist(toset(var.cidrs)))` drops duplicate 10.0.1.0/24.
```

### Step 7 — Custom application name

Change slug input.

```bash
terraform apply -auto-approve -var='application=Claims Portal'
```

**Validate**

```text
slug becomes claims-portal.
```

### Step 8 — jsonencode output

Structured string for policies/user_data.

```bash
terraform output -json results | jq .json
```

**Validate**

```text
JSON string with name and cidrs.
```

### Step 9 — Invalid CIDR drill

Functions do not validate business rules.

```bash
terraform console
```

**Validate**

```text
Note: overlapping cidrs still encode — external validation needed.
```

### Step 10 — fmt and validate

Keep expressions readable.

```bash
terraform fmt
terraform validate
```

**Validate**

```text
Formatted and valid.
```

## Design notes

Functions are pure — they cannot call APIs or create resources. Unknown values (computed at apply) may defer evaluation. Use `validation` blocks on variables for constraints functions cannot enforce (CIDR overlap, naming regex). Keep complex locals readable with intermediate names.

## Done when

- [ ] Used terraform console for three functions
- [ ] Applied with custom application name
- [ ] Interpreted jsonencode output

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| `Invalid function argument` | Type mismatch | Wrap with tolist/toset |
| Sensitive in jsonencode | Mark outputs carefully | Structure non-sensitive fields |

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
*Deep dive: [docs/functions/README.md](../docs/functions/README.md) · Next: [Lab 14 — Dynamic blocks](lab14-dynamic-blocks.md)*

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

## Reference — ownership questions (continued 3)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.
