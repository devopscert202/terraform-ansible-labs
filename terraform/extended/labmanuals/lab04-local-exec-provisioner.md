# Lab 04 — Local-exec provisioner

> **Goal:** Run a local shell command during resource creation using `terraform_data` and `local-exec`.
> **Time:** ~30 min · **Directory:** `terraform/extended/labs/lab04-local-exec-provisioner/`

## Learning objectives

After completing this lab you will be able to:

- Describe when `local-exec` runs in the resource lifecycle
- Use `terraform_data` as a provisioner host without cloud resources
- Predict re-apply behavior vs taint/replace
- Test provisioner commands outside Terraform before embedding
- Explain why provisioners are an escape hatch

## Architecture

`terraform_data` with a `local-exec` provisioner runs a shell command on the machine executing Terraform — your laptop or CI agent.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
}

variable "message" {
  type    = string
  default = "local-exec completed"
}

resource "terraform_data" "local_action" {
  input = var.message
  provisioner "local-exec" {
    command = "printf '%s\n' '${self.input}'"
  }
}

output "message" {
  value = terraform_data.local_action.output
}
```

```text
Terraform CLI host
  └─ terraform apply
       └─ terraform_data.local_action (create)
            └─ provisioner local-exec
                 └─ printf message to stdout
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | Read main.tf | local-exec block |
| 2 | Local test | printf works |
| 3 | Apply | Script runs on create |
| 4 | Re-apply | No re-run |
| 5 | Taint | Provisioner runs again |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab04-local-exec-provisioner
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Open the lab directory

No cloud providers in this module.

```bash
cd terraform/extended/labs/lab04-local-exec-provisioner
ls
```

**Validate**

```text
Files include `main.tf` only.
```

### Step 2 — Study provisioner block

Note `self.input` references the resource input attribute.

```bash
grep -A8 'provisioner "local-exec"' main.tf
```

**Validate**

```text
Command uses `printf` with interpolated `self.input`.
```

### Step 3 — Test command locally

Run the same printf outside Terraform first.

```bash
printf '%s\n' 'local-exec completed'
```

**Validate**

```text
Line `local-exec completed` printed.
```

### Step 4 — Initialize

No external providers required beyond built-ins.

```bash
terraform init
```

**Validate**

```text
Terraform has been successfully initialized.
```

### Step 5 — Validate

Confirm provisioner syntax is accepted.

```bash
terraform validate
```

**Validate**

```text
Configuration is valid.
```

### Step 6 — Plan

Expect create of `terraform_data.local_action`.

```bash
terraform plan
```

**Validate**

```text
Plan shows `+ terraform_data.local_action`.
```

### Step 7 — Apply and watch stdout

Provisioner runs during create.

```bash
terraform apply -auto-approve
```

**Validate**

```text
Stdout shows printf output; apply succeeds.
```

### Step 8 — Re-apply behavior

Provisioners do not re-run on in-place update.

```bash
terraform apply -auto-approve
```

**Validate**

```text
No changes — provisioner not re-executed.
```

### Step 9 — Taint and replace

Force recreate to see provisioner again.

```bash
terraform taint terraform_data.local_action
terraform apply -auto-approve
```

**Validate**

```text
Provisioner runs again on replacement.
```

### Step 10 — Inspect state

Provisioner output is not stored in state by default.

```bash
terraform state show terraform_data.local_action
```

**Validate**

```text
Shows `input` attribute; no script output.
```

### Step 11 — Custom message

Override default variable.

```bash
terraform apply -auto-approve -var='message=hello from lab04'
```

**Validate**

```text
Printf displays custom message during apply.
```

## Design notes

HashiCorp recommends cloud-init, images, or config management over provisioners. `local-exec` is appropriate for one-shot local actions (generating a file, calling an internal API) tied to infrastructure lifecycle. Commands inherit the operator's environment and permissions — audit them like production shell access. Failed create-time provisioners taint the resource.

## Done when

- [ ] Observed printf during apply
- [ ] Confirmed second apply made no changes without taint
- [ ] Explained one appropriate and one inappropriate use of local-exec

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| Provisioner never runs | Resource already exists | Taint or destroy first |
| `self.input` empty | Input not set | Check variable default |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/provisioners/README.md](../docs/provisioners/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/provisioners/README.md](../docs/provisioners/README.md) · Next: [Lab 05 — Remote-exec provisioner](lab05-remote-exec-provisioner.md)*

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
