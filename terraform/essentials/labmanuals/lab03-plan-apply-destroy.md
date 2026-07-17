# Lab 03 — Plan, Apply, and Destroy

| | |
|---|---|
| **Goal** | Execute the full Terraform lifecycle on a safe Random provider resource with no AWS cost. |
| **Time** | 25–35 minutes |
| **Difficulty** | Beginner |
| **Files** | `terraform/essentials/labs/lab03-plan-apply-destroy/main.tf` |

## Overview

Before managing production AWS infrastructure, you need confidence in the core workflow: **init → plan → apply → destroy**. Lab 03 uses `random_string.example` so you can practice typing `yes`, reading plan symbols (`+ create`), and observing state changes without cloud spend or credentials.

The Random provider generates a 12-character lowercase string. After apply, Terraform records the result in state and prints `generated_value`. Destroy removes the resource and clears state — the same pattern you will use for EC2 in Lab 02.

## Learning objectives

After completing this lab you will be able to:

- Interpret plan output (`+`, `-`, `~` symbols)
- Apply changes with explicit confirmation
- Read Terraform outputs after apply
- Destroy all managed resources cleanly
- Explain the difference between plan (read-only) and apply (mutating)

## Prerequisites checklist

- [ ] Terraform 1.5+ installed
- [ ] Lab 01 completed (understanding of `terraform init`)
- [ ] No AWS credentials required

## What you will build

| Object | Provider | Cost |
|--------|----------|------|
| `random_string.example` | hashicorp/random | None |
| Output `generated_value` | — | — |
| `terraform.tfstate` | local backend | — |

## Exercise index

| Exercise | Topic | Steps |
|----------|-------|-------|
| 1 | Initialize | 1.1 – 1.2 |
| 2 | Plan (read-only) | 2.1 – 2.2 |
| 3 | Apply | 3.1 – 3.2 |
| 4 | Re-plan (no changes) | 4.1 |
| 5 | Destroy | 5.1 – 5.2 |

---

## Exercise 1 — Initialize

### Step 1.1 — Navigate to lab directory

```bash
cd terraform/essentials/labs/lab03-plan-apply-destroy
```

**Validate:** `cat main.tf` shows `resource "random_string" "example"`.

**What happened:** Isolated root module — state stays in this folder.

### Step 1.2 — Run init

```bash
terraform init
```

**Validate:**

```
Terraform has been successfully initialized!
```

**What happened:** Downloaded `hashicorp/random` ~> 3.0 per `required_providers`.

---

## Exercise 2 — Plan (read-only)

### Step 2.1 — Run terraform plan

```bash
terraform plan
```

**Validate:** Summary line:

```
Plan: 1 to add, 0 to change, 0 to destroy.
```

**What happened:** Plan computed that `random_string.example` does not exist in state and must be created. No cloud APIs called.

### Step 2.2 — Inspect resource block in plan

Find the section:

```
  # random_string.example will be created
  + resource "random_string" "example" {
      + length  = 12
      + lower   = true
      + result  = (known after apply)
      ...
    }
```

**Validate:** `+` prefix indicates **create**. `result` is unknown until apply.

**What happened:** The `+` symbol is your cue that apply will create new infrastructure.

---

## Exercise 3 — Apply

### Step 3.1 — Run terraform apply

```bash
terraform apply
```

Terraform shows the plan again. Type exactly:

```
yes
```

**Validate:**

```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

generated_value = "<12 lowercase letters>"
```

**What happened:** Random provider generated the string; state file written with resource attributes.

### Step 3.2 — Re-read output

```bash
terraform output generated_value
```

**Validate:** Same 12-character string as apply output.

**What happened:** Outputs persist in state until the resource is destroyed.

---

## Exercise 4 — Re-plan (no changes)

### Step 4.1 — Plan again

```bash
terraform plan
```

**Validate:**

```
No changes. Your infrastructure matches the configuration.
```

Or: `Plan: 0 to add, 0 to change, 0 to destroy.`

**What happened:** Configuration matches state — Terraform has nothing to do. This is the desired steady state.

---

## Exercise 5 — Destroy

### Step 5.1 — Run terraform destroy

```bash
terraform destroy
```

Review the destruction plan. Type `yes`.

**Validate:**

```
Destroy complete! Resources: 0 added, 0 changed, 1 destroyed.
```

**What happened:** Resource removed from state. The random string ceases to be managed (there is no persistent cloud object).

### Step 5.2 — Verify empty state

```bash
terraform state list
```

**Validate:** No output (empty state).

**What happened:** Ready for next student or re-run from scratch.

---

## Done when

- [ ] `terraform init` succeeded
- [ ] First plan showed **1 to add**
- [ ] Apply printed `generated_value`
- [ ] Second plan showed **no changes**
- [ ] Destroy removed the resource
- [ ] `terraform state list` is empty

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `terraform validate` before init | Providers not installed | Run `terraform init` |
| Plan shows 0 to add but no state | Already applied | Run `destroy` or continue from current state |
| `Error asking for approval` | Non-interactive terminal | Use `terraform apply -auto-approve` only when appropriate |
| Different output each apply | Expected — random value | Normal behavior |
| Destroy wants to destroy 0 | Already destroyed | Confirm `terraform state list` |
| Lock file mismatch | Corrupted init | `rm -rf .terraform` and `terraform init` |

## Cleanup

```bash
cd terraform/essentials/labs/lab03-plan-apply-destroy
terraform destroy
```

Optional:

```bash
rm -f terraform.tfstate terraform.tfstate.backup
```

## Key takeaways

1. **Plan is read-only** — safe to run anytime.
2. **`+`** means create; always review before `yes`.
3. **Apply** updates state; **destroy** clears managed resources.
4. **No changes** plan means config matches state.
5. Same workflow applies to AWS resources — practice here first.

## Next steps

- Read [docs/04-workflow/README.md](../docs/04-workflow/README.md)
- Open [html/workflow.html](../html/workflow.html)
- Continue to [Lab 04 — Fmt & Validate](lab04-fmt-validate.md)
