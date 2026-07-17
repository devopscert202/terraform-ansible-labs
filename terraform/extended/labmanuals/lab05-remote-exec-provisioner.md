# Lab 05 — remote-exec provisioner

> **Goal:** Connect to an existing SSH host without storing credentials in source.
> **Time:** ~20 min · **Files:** `labs/lab05-remote-exec-provisioner/`

## Before you start

- Terraform 1.5 or newer is installed (`terraform version`).
- For this lab, use an AWS profile or IAM role; do not add access keys to `.tf` files.
- Run every command from `terraform/extended/labs/lab05-remote-exec-provisioner`.

## Steps

### Step 1 — Inspect the configuration

Read `main.tf` and any `variables.tf` or example backend file. Identify inputs, outputs, and the ownership boundary before executing Terraform.

```bash
cd ../labs/lab05-remote-exec-provisioner
ls
```

**Validate**

```text
The lab configuration and its supporting files are present.
```

### Step 2 — Initialize and validate

Initialization installs only the providers declared by this root module. Backend suite labs intentionally use `-backend=false` for local syntax validation; initialize their actual backend only after completing the backend prerequisites.

```bash
terraform init && terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

### Step 3 — Review the execution boundary

A plan is a proposal, not approval to create resources. Read additions, changes, destroys, provider region, and every input value. Stop if the target account, state location, or resource scope is unexpected.

```bash
terraform plan -var-file=terraform.tfvars # after copying the example and supplying a reachable host
```

**Validate**

```text
The plan matches the intended lab outcome and contains no unexpected destroy operations.
```

### Step 4 — Apply only when appropriate

Labs that only transform data can be applied safely after plan review. AWS examples must be applied only in an approved training account. Remote-exec needs a host you own and can reach; it does not create that host.

```bash
terraform apply
```

**Validate**

```text
Terraform reports Apply complete and the documented outputs are shown.
```

## Provisioner decision check

Before using a provisioner, decide whether cloud-init, an immutable image, a CI deployment step, or Ansible expresses the intent more reliably. Provisioners couple an imperative command to resource lifecycle and can fail because of network timing, shell differences, or non-idempotent commands. Keep each command short, observable, and safe to rerun.

## Done when

- [ ] You ran the validation command and reviewed its success result.
- [ ] You can explain what state this lab reads or writes.
- [ ] Any cloud resource created for the lab has a documented cleanup action.

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry access, or an unsupported Terraform version | Check `terraform version`, network access, then rerun `terraform init`. |
| Plan requests an unexpected resource | Wrong workspace, variable file, region, or state | Stop; inspect `terraform workspace show`, inputs, and backend settings. |
| AWS request is denied | Profile/role lacks access or points at the wrong account | Verify `AWS_PROFILE` and `aws sts get-caller-identity`; request least-privilege training access. |
| Backend initialization fails | Bucket, region, IAM permissions, or key configuration is wrong | Validate the pre-created bucket and use the matching `backend.hcl.example` values. |

## Cleanup

```bash
Remove any local test artifacts and do not commit state or private tfvars.
```

Remove generated state, plans, and copied `terraform.tfvars` files if they contain non-public information. Do not commit them.

---
*Deep dive: [docs/provisioners/README.md](docs/provisioners/README.md). Next: [Lab 06](lab06-workspaces.md)*
