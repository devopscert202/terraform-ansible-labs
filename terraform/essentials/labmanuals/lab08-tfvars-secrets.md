# Lab 08 — tfvars, Validation, and Secrets

> **Goal:** Load non-secret values from `terraform.tfvars`, enforce input rules with **variable validation** blocks, and supply sensitive values through environment variables — never committed files.
> **Time:** ~50 min · **Difficulty:** Intermediate · **Files:** `labs/lab08-tfvars-secrets/`

## Overview

Production Terraform receives configuration from multiple sources: variable defaults, `terraform.tfvars`, `-var` flags, and `TF_VAR_*` environment variables. Secrets belong in the last category (or a secrets manager) — **never** in git-tracked `.tfvars` files.

This lab has **no cloud resources** — only validated variables, a `locals` map, and outputs. You will copy a safe example tfvars file, export a fake phone number via `TF_VAR_phone_number`, run validation, observe sensitive redaction in plans, and deliberately trigger validation errors to see Terraform reject bad input.

## Learning objectives

- Auto-load values from `terraform.tfvars` for non-sensitive configuration
- Write and test `validation` blocks on input variables
- Pass sensitive values with `TF_VAR_*` environment variables
- Observe sensitive output redaction in `plan` and `terraform output`
- Understand that sensitive marking does not remove values from state

## Prerequisites

- [ ] Terraform 1.5+ installed (`terraform version`)
- [ ] Lab 05 complete (variables fundamentals)
- [ ] Lab 04 exposure to sensitive outputs helpful
- [ ] Working directory: `terraform/essentials/labs/lab08-tfvars-secrets`

## What you will build

```
terraform/essentials/labs/lab08-tfvars-secrets/
├── main.tf                      # locals, outputs (no resources)
├── variables.tf                 # validation + sensitive phone_number
├── terraform.tfvars             # copied from example (non-secrets only)
├── terraform.tfvars.example     # safe committed template
└── terraform.tfstate            # may be created after apply
```

```
  terraform.tfvars          TF_VAR_phone_number (env)
  ┌────────────────┐        ┌─────────────────────┐
  │ cloud, dept,   │        │ example-only        │
  │ cost_code, ip  │        │ (never in git)      │
  └───────┬────────┘        └──────────┬──────────┘
          │                            │
          └──────────┬─────────────────┘
                     ▼
              variables.tf (validation)
                     │
                     ▼
              outputs (phone sensitive)
```

---

## Exercise 1 — Read variables and validation rules

<a id="ex1"></a>

### Step 1.1 — Navigate to the lab directory

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab08-tfvars-secrets
```

**Validate**

```bash
ls -la
```

Directory contains `main.tf`, `variables.tf`, and `terraform.tfvars.example`.

**What happened:** This root module demonstrates input hygiene without provisioning AWS resources.

### Step 1.2 — Display variables.tf validation rules

```bash
cat variables.tf
```

**Validate** — file includes validation for:

| Variable | Rule |
|----------|------|
| `cloud` | Must be `aws`, `azure`, `gcp`, or `vmware` (lowercase) |
| `department` | Must be all lowercase |
| `cost_code` | Exactly three characters |
| `ip_address` | Valid IPv4 address |
| `phone_number` | Marked `sensitive = true` |

**What happened:** `validation` blocks run at plan/apply time. Invalid values fail before any infrastructure changes.

### Step 1.3 — Display main.tf outputs

```bash
cat main.tf
```

**Validate** — `output "configuration"` exposes `cloud`, `department`, `cost_code`, and `ip_address`. `output "phone_number"` is marked `sensitive = true`.

**What happened:** Splitting sensitive and non-sensitive outputs lets automation consume safe metadata while redacting secrets.

---

## Exercise 2 — Configure values and secrets

<a id="ex2"></a>

### Step 2.1 — Copy the example tfvars file

```bash
cp terraform.tfvars.example terraform.tfvars
```

**Validate**

```bash
cat terraform.tfvars
```

Shows `cloud = "aws"`, `department = "platform"`, `cost_code = "123"`, `ip_address = "192.0.2.10"` — no `phone_number` line.

**What happened:** `terraform.tfvars` auto-loads non-secret values. TEST-NET IP `192.0.2.10` is documentation-safe (RFC 5737).

### Step 2.2 — Export sensitive value via environment

```bash
export TF_VAR_phone_number="example-only"
```

**Validate**

```bash
grep phone_number terraform.tfvars || echo "phone_number not in tfvars — good"
```

```text
phone_number not in tfvars — good
```

**What happened:** `TF_VAR_*` environment variables map to Terraform variables. Secrets stay out of committed files.

---

## Exercise 3 — Initialize and validate

<a id="ex3"></a>

### Step 3.1 — Run terraform init

```bash
terraform init
```

**Validate**

```text
Terraform has been successfully initialized!
```

No providers required — this lab uses only core Terraform functionality.

**What happened:** `init` still initializes the backend and prepares the working directory even without providers.

### Step 3.2 — Validate with correct inputs

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

**What happened:** `validate` checks syntax and internal references. Variable validation conditions run during plan/apply, not always during validate — plan is the real test.

---

## Exercise 4 — Plan and observe sensitive redaction

<a id="ex4"></a>

### Step 4.1 — Run terraform plan

```bash
terraform plan
```

**Validate** — plan summary includes:

```text
Plan: 0 to add, 0 to change, 0 to destroy.
```

No resources exist in this configuration.

**What happened:** Outputs still appear in plan because Terraform evaluates what output values will be after apply.

### Step 4.2 — Confirm sensitive output is redacted in plan

**Validate**

```text
+ phone_number = (sensitive value)
```

The literal `example-only` does **not** appear in plan output.

**What happened:** `sensitive = true` on the variable and output ensures CLI redaction. State may still store the value after apply.

---

## Exercise 5 — Apply and read outputs

<a id="ex5"></a>

### Step 5.1 — Apply configuration

```bash
terraform apply -auto-approve
```

**Validate**

```text
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

Outputs section shows `phone_number` redacted.

**What happened:** Apply with zero resources still evaluates outputs and updates state metadata.

### Step 5.2 — Reveal sensitive output deliberately

```bash
terraform output -raw phone_number
```

**Validate**

```text
example-only
```

**What happened:** `-raw` bypasses redaction for scripting. Use sparingly and never log the result in CI.

---

## Exercise 6 — Trigger validation failures

<a id="ex6"></a>

### Step 6.1 — Test invalid cloud value

```bash
terraform plan -var="cloud=AWS"
```

**Validate** — command fails with:

```text
Error: Invalid value for variable
```

And message containing:

```text
cloud must be aws, azure, gcp, or vmware in lowercase.
```

**What happened:** Validation blocks reject bad input before apply. Uppercase `AWS` fails the `contains()` check.

### Step 6.2 — Test invalid cost_code length

```bash
terraform plan -var="cost_code=1234"
```

**Validate** — error message contains:

```text
cost_code must contain exactly three characters.
```

**What happened:** `length(var.cost_code) == 3` enforces a fixed-width cost center code. Sensitive values still appear in state — treat `terraform.tfstate` as confidential.

---

## Exercise 7 — Cleanup secrets and state

<a id="ex7"></a>

### Step 7.1 — Destroy and remove local files

```bash
terraform destroy -auto-approve
```

**Validate**

```text
Destroy complete! Resources: 0 destroyed.
```

**What happened:** Clears state metadata for the next student.

### Step 7.2 — Unset secret and remove tfvars

```bash
unset TF_VAR_phone_number
```

**Validate**

```bash
echo ${TF_VAR_phone_number:-unset}
```

```text
unset
```

**What happened:** Clear secrets from the shell session when the lab ends.

### Step 7.3 — Remove local tfvars copy

```bash
rm -f terraform.tfvars
```

**Validate**

```bash
ls terraform.tfvars 2>&1
```

```text
ls: terraform.tfvars: No such file or directory
```

**What happened:** Delete environment-specific tfvars. Recreate from `.example` next time.

---

## Key takeaways

- **`terraform.tfvars`** auto-loads non-secret, environment-specific values
- **`TF_VAR_*`** environment variables inject secrets without writing files
- **`validation` blocks** reject bad input at plan time with clear error messages
- **`sensitive = true`** redacts CLI output but **not** state file contents
- Never commit `terraform.tfvars` with real secrets — use `.example` templates only

## Done when

- [ ] `terraform.tfvars` copied from example with safe values only
- [ ] `TF_VAR_phone_number` exported (not written to tfvars)
- [ ] `terraform validate` returned Success
- [ ] `terraform plan` showed public config and redacted `phone_number`
- [ ] `terraform apply` completed; `terraform output` showed `<sensitive>`
- [ ] At least one validation error reproduced (invalid `cloud`, `cost_code`, etc.)
- [ ] `terraform.tfvars` removed and `TF_VAR_phone_number` unset

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No value for required variable phone_number` | `TF_VAR_phone_number` not set | `export TF_VAR_phone_number="example-only"` |
| Validation error on valid `cloud` | Typo or uppercase | Use lowercase `aws` exactly |
| `cost_code` validation fails unexpectedly | Wrong length in tfvars | Ensure exactly 3 characters in `terraform.tfvars` |
| Sensitive value visible in plan | `sensitive` not set | Check `variables.tf` and output block |
| `terraform.tfvars` not loaded | Wrong filename or directory | File must be named `terraform.tfvars` in root module |
| `ip_address` validation fails for valid IP | IPv6 address supplied | Lab validates IPv4 only |

## Cleanup

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab08-tfvars-secrets
terraform destroy -auto-approve 2>/dev/null || true
unset TF_VAR_phone_number
rm -f terraform.tfvars terraform.tfstate terraform.tfstate.backup
```

Never commit `terraform.tfvars` or state files from this lab.

## Next steps

- [Foundations (interactive HTML)](../html/foundations.html)
- [Variables and validation doc](../docs/04-variables/README.md)
- Return to [Lab 01](lab01-providers-init.md) for a refresher or proceed to advanced modules in the curriculum

---
*Source: Terraform Essentials bootcamp · L10 AP-03 · End of Essentials labs 01–08*
