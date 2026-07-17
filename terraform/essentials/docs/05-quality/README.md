# 05 — Quality

## Overview

Infrastructure code deserves the same quality discipline as application code. Terraform provides built-in commands — `fmt` and `validate` — that catch formatting inconsistencies and configuration errors before you touch a cloud API. In mature teams, these checks run in CI on every pull request.

This chapter extends Lab 04 with CI integration patterns, sensitive output handling, and pre-apply checklists. Quality gates are cheap insurance: `validate` runs in seconds and prevents embarrassing plan failures in shared pipelines.

### Why this matters for beginners

A missing argument or typo in a resource block might not be obvious until `plan` — or worse, mid-`apply`. Running `terraform validate` after every edit builds a habit that saves hours of debugging. Similarly, `terraform fmt` eliminates style debates in code review.

---

## Key concepts

| Concept | Tool | Purpose |
|---------|------|---------|
| Canonical formatting | `terraform fmt` | Consistent HCL style |
| Static analysis | `terraform validate` | Syntax + internal consistency |
| Format check (CI) | `terraform fmt -check` | Fail build on unformatted files |
| Sensitive values | `sensitive = true` | Redact CLI output |
| Lock file | `.terraform.lock.hcl` | Reproducible provider versions |
| Pre-commit hooks | External (optional) | Auto-fmt before commit |

---

## Quality gate workflow

```
  Developer edit (.tf)
         │
         ▼
  ┌─────────────┐     fail    ┌──────────────┐
  │ terraform fmt│────────────▶│ fix formatting│
  └──────┬──────┘             └──────────────┘
         │ pass
         ▼
  ┌─────────────┐     fail    ┌──────────────┐
  │terraform init│────────────▶│ install providers│
  └──────┬──────┘             └──────────────┘
         │ pass
         ▼
  ┌─────────────┐     fail    ┌──────────────┐
  │   validate   │────────────▶│ fix config errors │
  └──────┬──────┘             └──────────────┘
         │ pass
         ▼
  ┌─────────────┐
  │     plan      │
  └─────────────┘
```

---

## Lab 04 walkthrough

### Configuration

`labs/lab04-fmt-validate/main.tf`:

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

resource "random_string" "formatted_example" {
  length  = 10
  special = true
  numeric = true
  upper   = true
}

output "formatted_example" {
  value     = random_string.formatted_example.result
  sensitive = true
}
```

### Step 1 — Initialize

```bash
cd terraform/essentials/labs/lab04-fmt-validate
terraform init
```

### Step 2 — Format

```bash
terraform fmt
```

`fmt` rewrites files to standard style (2-space indent, aligned `=`). No output means already formatted.

### Step 3 — Validate

```bash
terraform validate
```

Expected:

```
Success! The configuration is valid.
```

### What validate checks

- Block structure and argument types
- Reference validity (`var.x`, `resource.y.z`)
- Provider configuration schema
- **Does not** call cloud APIs
- **Does not** verify credentials

### Step 4 — Apply and test sensitive output

```bash
terraform apply
terraform output formatted_example
# (sensitive value)

terraform output -raw formatted_example
# reveals actual 10-character string
```

### Step 5 — Destroy

```bash
terraform destroy
```

---

## CI integration examples

### Shell script for PR checks

```bash
#!/usr/bin/env bash
set -euo pipefail

terraform fmt -check -recursive .
terraform init -backend=false -input=false
terraform validate
```

### GitHub Actions (conceptual)

```yaml
jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
      - run: terraform fmt -check -recursive
      - run: terraform init -backend=false
      - run: terraform validate
```

For AWS plan in CI, use OIDC or short-lived credentials — never commit keys.

---

## Sensitive outputs and variables

```hcl
output "db_password" {
  value     = random_password.db.result
  sensitive = true
}

variable "api_token" {
  type      = string
  sensitive = true
}
```

**Important:** `sensitive = true` redacts **CLI display** only. Values still exist in **state**. Encrypt remote backends and restrict state access.

---

## fmt style rules (examples)

Before fmt:

```hcl
resource "random_string" "x" {
length=10
special=true
}
```

After fmt:

```hcl
resource "random_string" "x" {
  length  = 10
  special = true
}
```

---

## Common mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| validate before init | Provider schema missing | Run `init` first |
| Ignoring fmt in CI | Inconsistent reviews | Add `fmt -check` |
| Assuming validate catches all errors | Runtime API errors at apply | Still review plan |
| `sensitive` on output only | Secret still in state | Protect state backend |
| Not committing lock file | Different provider versions on CI | Commit `.terraform.lock.hcl` |
| Skipping validate in hurry | Broken main branch | Make validate mandatory |

---

## Pre-apply checklist

- [ ] `terraform fmt` (or `-check` in CI)
- [ ] `terraform init` (if providers changed)
- [ ] `terraform validate` succeeds
- [ ] `AWS_PROFILE` set for AWS labs
- [ ] `terraform plan` reviewed — note `+/-/~` counts
- [ ] Destroy scheduled after verification

---

## Links

| Resource | Path |
|----------|------|
| Lab 04 manual | [labmanuals/lab04-fmt-validate.md](../../labmanuals/lab04-fmt-validate.md) |
| HTML: Workflow | [html/workflow.html](../../html/workflow.html) |
| Previous | [04-workflow/README.md](../04-workflow/README.md) |
| Next | [06-variables/README.md](../06-variables/README.md) |

---

## Hands-on lab

**[Lab 04 — Fmt & Validate](../../labmanuals/lab04-fmt-validate.md)** — No AWS required.

---

## Key takeaways

1. **fmt** standardizes style; **validate** catches structural errors.
2. Run both **before every plan** in learning and production.
3. **Sensitive** flags hide values in normal CLI output, not in state.
4. CI should run `fmt -check` and `validate` on every change.
5. Quality gates are free — use them consistently.

---

## Next steps

Read [06 — Variables](../06-variables/README.md) for inputs, locals, and tfvars.
