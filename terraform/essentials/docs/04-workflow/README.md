# 04 — Workflow

## Overview

The Terraform workflow is a disciplined loop: **initialize** plugins, **validate** configuration, **plan** changes, **apply** approved changes, and **destroy** when tearing down. Quality gates (`fmt`, `validate`) belong in every run and in CI pipelines. This chapter maps each command to Lab 03 (lifecycle) and Lab 04 (quality).

For beginners, the workflow is the safety rail: `plan` is read-only preview; `apply` mutates infrastructure. Skipping plan review is the most common cause of accidental production outages.

### Why this matters for beginners

Terraform will destroy resources if you remove them from configuration. The plan output is your last chance to catch `1 to destroy` before typing `yes`. Labs 03 and 04 build muscle memory: init → validate → plan → apply → verify → destroy.

---

## Key concepts

| Command | Modifies cloud? | Modifies state? | Lab |
|---------|-----------------|-----------------|-----|
| `terraform init` | No | No (setup only) | 01, 03 |
| `terraform fmt` | No | No | 04 |
| `terraform validate` | No | No | 01, 04 |
| `terraform plan` | No | No | 03 |
| `terraform apply` | Yes | Yes | 03 |
| `terraform destroy` | Yes | Yes | 03 |

---

## Core workflow diagram

```
                    ┌──────────────┐
                    │ terraform init│
                    └──────┬───────┘
                           ▼
              ┌────────────────────────┐
              │ terraform fmt (optional) │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ terraform validate      │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ terraform plan          │◀── read-only preview
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ terraform apply         │◀── type "yes"
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ verify outputs / console  │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │ terraform destroy       │◀── cleanup (AWS labs)
              └────────────────────────┘
```

---

## Lab 03 — Plan, apply, destroy

Configuration: `labs/lab03-plan-apply-destroy/main.tf`

```hcl
resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}

output "generated_value" {
  value = random_string.example.result
}
```

### Initialize

```bash
cd terraform/essentials/labs/lab03-plan-apply-destroy
terraform init
```

Expected tail:

```
Terraform has been successfully initialized!
```

### Plan

```bash
terraform plan
```

Expected:

```
Plan: 1 to add, 0 to change, 0 to destroy.

  # random_string.example will be created
  + resource "random_string" "example" {
      + length  = 12
      + result  = (known after apply)
      ...
    }
```

### Apply

```bash
terraform apply
```

Review plan, type `yes`.

Expected:

```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

generated_value = "abcdefghijkl"
```

### Destroy

```bash
terraform destroy
```

Type `yes`. Expected: `1 destroyed`.

---

## Lab 04 — Format and validate

Configuration: `labs/lab04-fmt-validate/main.tf`

```hcl
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

### Format

```bash
cd terraform/essentials/labs/lab04-fmt-validate
terraform init
terraform fmt
```

If files need formatting, `fmt` prints their names. Re-run until silent.

CI pattern:

```bash
terraform fmt -check -recursive .
# Non-zero exit if formatting needed
```

### Validate

```bash
terraform validate
```

Expected: `Success! The configuration is valid.`

### Sensitive output behavior

After apply:

```bash
terraform output formatted_example
# (sensitive value)

terraform output -raw formatted_example
# actual string value
```

---

## Reading plan symbols

| Symbol | Meaning |
|--------|---------|
| `+` | Create |
| `-` | Destroy |
| `~` | Update in-place |
| `-/+` | Destroy and recreate |
| `<=` | Read (data source) |

---

## Plan internals (simplified)

```
1. Refresh state  ──▶  Query provider APIs for current attributes
2. Diff           ──▶  Compare state + config
3. Graph          ──▶  Order actions by dependencies
4. Display        ──▶  Print human-readable plan
```

Drift example: if someone changes a tag in the AWS console, the next plan may show `~ tags`.

---

## Useful flags

```bash
terraform plan -out=tfplan          # Save plan for reviewed apply
terraform apply tfplan              # Apply exact saved plan
terraform apply -auto-approve       # Skip prompt (CI only)
terraform plan -destroy             # Plan deletion without destroy cmd
terraform apply -refresh-only       # Update state only
terraform plan -target=aws_instance.web  # Limit scope (emergency only)
```

---

## CI/CD pipeline pattern

```yaml
# Pseudocode pipeline stages
- terraform fmt -check -recursive
- terraform init -backend=false    # validate-only in CI
- terraform validate
- terraform plan -out=plan.tfplan
# manual approval gate
- terraform apply plan.tfplan
```

---

## Common mistakes

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| `apply` without reading plan | Unintended deletes | Always review `+/-/~` |
| `validate` before `init` | Provider errors | init first |
| Skipping `destroy` on AWS | Billing | Add destroy to checklist |
| `-auto-approve` locally | Accidental changes | Type `yes` manually when learning |
| Editing state instead of re-applying | Orphan resources | Use workflow commands |
| Running from wrong directory | Wrong state file | Verify `pwd` and lab folder |

---

## Evidence checklist (labs)

After each AWS lab, record:

- [ ] Terraform version (`terraform version`)
- [ ] Plan summary (N add / change / destroy)
- [ ] Key output values (instance_id, vpc_id, etc.)
- [ ] Destroy confirmation (`0 destroyed` remaining resources)

---

## Links

| Resource | Path |
|----------|------|
| Lab 03 | [labmanuals/lab03-plan-apply-destroy.md](../../labmanuals/lab03-plan-apply-destroy.md) |
| Lab 04 | [labmanuals/lab04-fmt-validate.md](../../labmanuals/lab04-fmt-validate.md) |
| HTML: Workflow | [html/workflow.html](../../html/workflow.html) |
| Previous | [03-resources/README.md](../03-resources/README.md) |
| Next | [05-quality/README.md](../05-quality/README.md) |

---

## Hands-on labs

1. **[Lab 03](../../labmanuals/lab03-plan-apply-destroy.md)** — Full lifecycle with `random_string`.
2. **[Lab 04](../../labmanuals/lab04-fmt-validate.md)** — `fmt`, `validate`, sensitive outputs.

---

## Key takeaways

1. **init** prepares; **plan** previews; **apply** executes; **destroy** cleans up.
2. **fmt** and **validate** are fast checks — run them every time.
3. Plan output symbols (`+`, `-`, `~`) are your safety review.
4. Lab 03 proves the loop without AWS cost.
5. Always **destroy** AWS resources when finished.

---

## Next steps

Continue to [05 — Quality](../05-quality/README.md) for expanded quality practices, then [06 — Variables](../06-variables/README.md).
