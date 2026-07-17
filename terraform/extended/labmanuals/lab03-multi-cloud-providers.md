# Lab 03 — Multi-cloud providers

> **Goal:** Initialize explicitly constrained provider plugins and inspect multi-provider composition.
> **Time:** ~25 min · **Directory:** `terraform/extended/labs/lab03-multi-cloud-providers/`

## Learning objectives

After completing this lab you will be able to:

- Declare multiple `required_providers` in one root module
- Configure `provider "aws"` with `var.aws_region` while leaving `provider "random"` empty
- Explain which provider owns which resource in a composite graph
- Read `provider_composition` output combining region and `random_pet` id
- Use `.terraform.lock.hcl` to reason about reproducible provider versions

## Architecture

This root module composes **two providers**: `hashicorp/aws` for regional context and `hashicorp/random` for a deterministic-but-unique label. Only `random_pet` creates a managed object; AWS provider initialization proves multi-provider graphs work.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }
provider "random" {}

resource "random_pet" "label" { length = 2 }

output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}

# variables.tf
variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region used by the AWS provider."
}
```

```text
┌──────────────────┐     ┌─────────────────┐
│ provider aws     │     │ provider random │
│ region=var.aws_  │     │ (no config)     │
│     region       │     └────────┬────────┘
└────────┬─────────┘              │
         │ (context only)         ▼
         │              ┌─────────────────┐
         └─────────────►│ random_pet.label│
                        └────────┬────────┘
                                 ▼
                        output provider_composition
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | Read providers | Identify aws + random pins |
| 2 | Init | Both plugins downloaded |
| 3 | Plan | One random_pet addition |
| 4 | Apply | Output shows region + label |
| 5 | State | Single resource address |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab03-multi-cloud-providers
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Navigate to the lab directory

Confirm all configuration files are present.

```bash
pwd
ls -la
```

**Validate**

```text
You are in `terraform/extended/labs/lab03-multi-cloud-providers`.
```

### Step 2 — Read provider constraints

Open `main.tf` and note `required_providers` pins for `aws` and `random`.

```bash
grep -A6 'required_providers' main.tf
```

**Validate**

```text
Both `hashicorp/aws` (~> 5.0) and `hashicorp/random` (~> 3.0) are declared.
```

### Step 3 — Inspect the region variable

`variables.tf` defines `aws_region` — the only AWS input.

```bash
cat variables.tf
```

**Validate**

```text
`aws_region` defaults to `us-east-1` with a description.
```

### Step 4 — Review outputs

The output merges region and generated pet name.

```bash
grep -A4 'output "provider_composition"' main.tf
```

**Validate**

```text
Output references `var.aws_region` and `random_pet.label.id`.
```

### Step 5 — Format configuration

Run fmt before init — team hygiene.

```bash
terraform fmt -check
terraform fmt
```

**Validate**

```text
No diff or formatting applied successfully.
```

### Step 6 — Initialize providers

Init downloads both provider plugins.

```bash
terraform init
```

**Validate**

```text
Success message lists `hashicorp/aws` and `hashicorp/random`.
```

### Step 7 — Validate types

Static analysis before any plan.

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

### Step 8 — Inspect lock file

Provider versions are pinned in `.terraform.lock.hcl`.

```bash
grep -E 'aws|random' .terraform.lock.hcl | head -6
```

**Validate**

```text
Lock file records provider hashes for reproducible init.
```

### Step 9 — Plan changes

Expect one `random_pet` to be created.

```bash
terraform plan
```

**Validate**

```text
Plan shows `+ random_pet.label` and output preview.
```

### Step 10 — Apply safely

Creates only the random pet — no VPC or EC2.

```bash
terraform apply
```

**Validate**

```text
Apply complete; `provider_composition` output displayed.
```

### Step 11 — Verify state

State should contain exactly one resource address.

```bash
terraform state list
terraform state show random_pet.label
```

**Validate**

```text
`random_pet.label` listed with `id` like two-word pet name.
```

### Step 12 — Optional region override

Practice variable injection without editing files.

```bash
terraform plan -var='aws_region=us-west-2'
```

**Validate**

```text
Plan output shows `aws_region` in composed output value.
```

## Design notes

Multiple providers coexist in one module graph. Only resources reference a provider implicitly (via resource type prefix) or explicitly (`provider = aws.west`). Here AWS is configured but creates no resources — useful for validating credentials and region before larger labs. Keep provider version constraints in `terraform` block; never pin versions only in docs.

## Done when

- [ ] Initialized aws and random providers
- [ ] Applied and captured `provider_composition` output
- [ ] Explained why AWS provider exists without AWS resources

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| `Failed to query available provider packages` | Registry/network | Retry init; check proxy |
| Random pet forces replacement each apply | `keepers` changed | Expected if inputs change |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate terraform.tfstate.backup
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/projects/README.md](../docs/projects/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/projects/README.md](../docs/projects/README.md) · Next: [Lab 04 — Local-exec provisioner](lab04-local-exec-provisioner.md)*

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
