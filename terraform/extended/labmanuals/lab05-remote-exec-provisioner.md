# Lab 05 — Remote-exec provisioner

> **Goal:** Connect over SSH and run commands on a remote host using `remote-exec` — without creating that host.
> **Time:** ~35 min · **Directory:** `terraform/extended/labs/lab05-remote-exec-provisioner/`

## Learning objectives

After completing this lab you will be able to:

- Configure a Terraform `connection` block for SSH
- Supply secrets via tfvars or `TF_VAR_*` — never commit keys
- Distinguish what Terraform creates vs what you provide
- Diagnose SSH failures before blaming Terraform
- Describe production alternatives to remote-exec

## Architecture

**Important:** This lab does **not** create the SSH target. You supply `host`, `user`, and `private_key_path` via `terraform.tfvars` (see example).

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
}

variable "host" {
  type        = string
  description = "Reachable SSH host. Supply with TF_VAR_host or terraform.tfvars."
}
variable "user" {
  type    = string
  default = "ec2-user"
}
variable "private_key_path" {
  type        = string
  sensitive   = true
  description = "Path to an SSH private key; do not commit it."
}

resource "terraform_data" "bootstrap" {
  input = var.host
  connection {
    type        = "ssh"
    host        = var.host
    user        = var.user
    private_key = file(pathexpand(var.private_key_path))
  }
  provisioner "remote-exec" {
    inline = ["echo Terraform remote-exec connected to $(hostname)"]
  }
}

output "target" {
  value = terraform_data.bootstrap.output
}
```

```hcl
# terraform.tfvars.example
host             = "203.0.113.10"
user             = "ec2-user"
private_key_path = "~/.ssh/lab-key.pem"
```

```text
Your laptop ──SSH──► target host
              remote-exec: echo hostname
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | Manual SSH | Host reachable |
| 2 | tfvars | Host/key configured |
| 3 | Apply | remote-exec succeeds |
| 4 | TF_VAR | Env injection works |
| 5 | Failure | Recognize taint on error |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab05-remote-exec-provisioner
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Prepare SSH target

Use a training EC2 instance or VM you control.

> Replace host/key with your values.

```bash
# Ensure SSH port open and key installed
ssh -i ~/.ssh/lab-key.pem ec2-user@YOUR_HOST hostname
```

**Validate**

```text
Manual SSH returns hostname without password prompt.
```

### Step 2 — Copy tfvars example

Never commit real keys or production hosts.

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit host and private_key_path
```

**Validate**

```text
`terraform.tfvars` exists locally and is gitignored.
```

### Step 3 — Review variables

Note `sensitive = true` on key path.

```bash
grep -A4 'variable "private_key_path"' main.tf
```

**Validate**

```text
Three variables: host, user, private_key_path.
```

### Step 4 — Review connection block

SSH transport for remote-exec.

```bash
grep -A6 'connection {' main.tf
```

**Validate**

```text
Uses `file(pathexpand(var.private_key_path))`.
```

### Step 5 — Initialize and validate

No cloud provider — connection only.

```bash
terraform init
terraform validate
```

**Validate**

```text
Valid configuration.
```

### Step 6 — Plan

Creates `terraform_data.bootstrap` only.

```bash
terraform plan
```

**Validate**

```text
Plan shows one terraform_data add; no EC2.
```

### Step 7 — Apply

Terraform opens SSH and runs inline command.

```bash
terraform apply
```

**Validate**

```text
Remote echo succeeds; output `target` shows host.
```

### Step 8 — Simulate failure

Wrong key should fail fast.

```bash
# Temporarily set bad key path in tfvars
terraform apply 2>&1 | head -20
```

**Validate**

```text
Permission denied or key error — apply fails; resource may be tainted.
```

### Step 9 — Restore and replace

Fix tfvars then taint if needed.

```bash
terraform taint terraform_data.bootstrap 2>/dev/null || true
terraform apply
```

**Validate**

```text
Successful reconnect message.
```

### Step 10 — Environment variables

CI pattern without tfvars file.

```bash
export TF_VAR_host=YOUR_HOST
export TF_VAR_private_key_path=~/.ssh/lab-key.pem
terraform plan
```

**Validate**

```text
Plan uses environment-injected variables.
```

### Step 11 — Security review

List what never belongs in git.

```bash
git status --ignored | grep tfvars || true
```

**Validate**

```text
Private tfvars and keys stay untracked.
```

## Design notes

Remote-exec couples infrastructure provisioning with configuration — fragile across network blips and AMI changes. Prefer SSM Run Command, Ansible, or golden images. The lab isolates connection mechanics so you recognize them in legacy modules. Scope security groups to bastion IPs; rotate lab keys after sessions.

## Done when

- [ ] Successful remote-exec against your host
- [ ] Configured tfvars without committing secrets
- [ ] Manual SSH test documented

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| `connection refused` | SG or wrong IP | Verify `ssh` manually |
| `permission denied (publickey)` | Key/user mismatch | Check tfvars paths |
| Host not set | Missing tfvars | Copy example file |

## Cleanup

```bash
terraform destroy -auto-approve
rm -f terraform.tfvars
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
*Deep dive: [docs/provisioners/README.md](../docs/provisioners/README.md) · Next: [Lab 06 — Workspaces](lab06-workspaces.md)*

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
