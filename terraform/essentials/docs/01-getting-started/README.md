# 01 — Getting Started with Terraform

## Overview

Terraform is an infrastructure-as-code (IaC) tool from HashiCorp. You write declarative configuration in HashiCorp Configuration Language (HCL), and Terraform figures out how to create, update, or delete cloud resources to match that configuration. For DevOps beginners, Terraform is often the first tool that makes infrastructure reproducible: the same `.tf` files that built dev can build staging and production with different input values.

This chapter introduces the mental model, directory layout, and safety practices used throughout the **Terraform Essentials** track. Every lab in `terraform/essentials/labs/` is self-contained with its own state file so you can experiment without affecting other exercises.

### Why this matters for beginners

Without IaC, infrastructure is built by clicking in a console or running one-off CLI commands. That approach does not scale: there is no audit trail, no peer review, and no easy way to recreate an environment after a failure. Terraform gives you a **version-controlled specification** of what should exist, a **plan** that shows changes before they happen, and **state** that links your configuration to real resource IDs.

---

## Key concepts

| Concept | Definition | Example in this track |
|---------|------------|----------------------|
| **Configuration** | `.tf` files describing desired infrastructure | `labs/lab01-providers-init/main.tf` |
| **Provider** | Plugin that talks to a cloud or service API | `hashicorp/aws`, `hashicorp/random` |
| **Resource** | Object Terraform creates and manages | `aws_instance`, `random_pet` |
| **Data source** | Read-only lookup of existing values | `data.aws_ami.ubuntu` (Lab 02) |
| **Output** | Value exported after apply | `output "lab_id"` |
| **State** | JSON mapping config addresses to real IDs | `terraform.tfstate` (created on apply) |
| **Working directory** | Folder where you run `terraform` commands | Each `labs/lab0X-*` folder |

---

## Architecture: how Terraform fits in your workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Developer      │     │  Terraform CLI   │     │  Cloud API      │
│  writes .tf     │────▶│  init/plan/apply │────▶│  AWS EC2, VPC…  │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  terraform.tfstate│
                        │  (ID mapping)     │
                        └──────────────────┘
```

Terraform does **not** run continuously. You invoke it deliberately. The CLI reads configuration, compares it to state (and refreshes from the API), then proposes or executes changes.

---

## Prerequisites checklist

Before starting Lab 01:

- [ ] Terraform **1.5.0 or later** installed
- [ ] AWS CLI installed (for AWS labs, starting Lab 02)
- [ ] An AWS account with permissions for EC2 (Lab 02+) or use Labs 01, 03, 04, 06, 08 without AWS
- [ ] `AWS_PROFILE` set to a named profile — **never** put `access_key` in `.tf` files

```bash
terraform version
```

Expected output includes `Terraform v1.5` or higher.

```bash
export AWS_PROFILE=training
aws sts get-caller-identity
```

Expected: JSON with `Account`, `Arn`, and `UserId`.

---

## Repository layout

```
terraform/essentials/
├── docs/           ← You are here (01-getting-started … 08-modules)
├── html/           ← Interactive diagrams (open in browser)
├── labmanuals/     ← Step-by-step lab guides
└── labs/           ← Runnable HCL per exercise
    ├── lab01-providers-init/
    ├── lab02-ec2/
    └── …
```

**Interactive reference:** [html/foundations.html](../html/foundations.html)  
**Hands-on lab:** [labmanuals/lab01-providers-init.md](../labmanuals/lab01-providers-init.md)

---

## Step-by-step: your first configuration

### Step 1 — Inspect Lab 01

Open `labs/lab01-providers-init/main.tf`. Notice three layers:

1. `terraform {}` block — version and provider requirements
2. `provider "aws" {}` — region only (no credentials)
3. `resource` and `output` blocks

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "random_pet" "lab_id" {
  length = 2
}

output "lab_id" {
  value = random_pet.lab_id.id
}
```

### Step 2 — Initialize

```bash
cd terraform/essentials/labs/lab01-providers-init
terraform init
```

`init` downloads provider plugins and creates `.terraform/` and `.terraform.lock.hcl`.

### Step 3 — Validate

```bash
terraform validate
```

Expected: `Success! The configuration is valid.`

### Step 4 — Plan (preview only)

```bash
terraform plan
```

Expected: `Plan: 1 to add, 0 to change, 0 to destroy` for `random_pet.lab_id`.

### Step 5 — Apply (optional for Lab 01)

```bash
terraform apply
```

Type `yes` when prompted. Note the `lab_id` output.

### Step 6 — Destroy when done

```bash
terraform destroy
```

---

## Version constraints explained

| Constraint | Meaning |
|------------|---------|
| `>= 1.5.0` | Terraform 1.5.0 or newer |
| `~> 5.0` | AWS provider 5.x (≥ 5.0, &lt; 6.0) |
| `~> 3.0` | Random provider 3.x |

The lock file `.terraform.lock.hcl` pins exact provider versions after `init`. Commit it in team projects.

---

## Authentication: AWS credential chain

The AWS provider uses the standard SDK credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID` — avoid in favor of profiles)
2. **`AWS_PROFILE`** pointing to `~/.aws/credentials`
3. IAM instance/profile role (on EC2, ECS, etc.)

```hcl
# ❌ NEVER do this
provider "aws" {
  access_key = "AKIA..."
  secret_key = "..."
}

# ✅ Correct — region only
provider "aws" {
  region = var.aws_region
}
```

---

## HCL syntax basics

```hcl
# Block syntax
block_type "label" "name" {
  argument = value
  nested_block {
    key = "value"
  }
}

# References
random_pet.lab_id.id          # resource attribute
var.aws_region                # input variable
local.common_tags             # local value
data.aws_ami.ubuntu.id        # data source attribute
```

Strings use double quotes. Lists use `[]`, maps use `{}`.

---

## Common mistakes

| Mistake | Why it fails | Fix |
|---------|--------------|-----|
| Running `validate` before `init` | Providers not installed | Run `terraform init` first |
| Credentials in `provider` block | Security risk; violates org policy | Use `AWS_PROFILE` |
| Editing `terraform.tfstate` by hand | Corrupts ID mapping | Use `terraform state` subcommands |
| Mixing lab directories | Shared/wrong state | `cd` into one lab folder only |
| Skipping `destroy` on AWS labs | Continued billing | Always destroy after verify |
| Committing `.terraform/` | Large binaries in git | Add to `.gitignore`; commit lock file only |

---

## What you will build in Lab 01

- A working directory with AWS and Random providers installed
- Lock file recording provider versions
- Valid configuration with no syntax errors
- (After apply) A `random_pet` resource and `lab_id` output

**No AWS resources are created** unless you run `apply` — and the only resource is `random_pet`, which has no cloud cost.

---

## Links

| Resource | Path |
|----------|------|
| Lab 01 manual | [labmanuals/lab01-providers-init.md](../labmanuals/lab01-providers-init.md) |
| Lab 01 files | [labs/lab01-providers-init/](../labs/lab01-providers-init/) |
| HTML: Foundations | [html/foundations.html](../html/foundations.html) |
| HTML: Index | [html/index.html](../html/index.html) |
| Next chapter | [02-providers/README.md](../02-providers/README.md) |

---

## Hands-on lab summary

| Lab | Topic | AWS required? |
|-----|-------|---------------|
| [Lab 01](../labmanuals/lab01-providers-init.md) | Providers & init | No (random only on apply) |
| [Lab 02](../labmanuals/lab02-ec2.md) | EC2 instance | Yes |

---

## Key takeaways

1. Terraform configuration is **declarative** — you describe the end state, not a script of API calls.
2. **`terraform init`** must run before validate/plan/apply whenever providers change.
3. **Never embed credentials** in HCL; use `AWS_PROFILE` or IAM roles.
4. Each lab directory is an **isolated root module** with its own state.
5. The lock file ensures **reproducible provider versions** across machines.

---

## Next steps

1. Complete [Lab 01](../labmanuals/lab01-providers-init.md) if you have not already.
2. Read [02 — Providers](../02-providers/README.md) for deeper provider concepts.
3. Open [foundations.html](../html/foundations.html) for the interactive provider/resource diagram.
