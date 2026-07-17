# Lab 11 — Remote state consumer

> **Goal:** Read a deliberately exposed output from an upstream state boundary.
> **Time:** ~20 min · **Files:** `labs/lab11-remote-state-consumer/`

## Before you start

- Terraform 1.5 or newer is installed (`terraform version`).
- No cloud credentials are required to validate this configuration.
- Run every command from `terraform/extended/labs/lab11-remote-state-consumer`.

## Steps

### Step 1 — Inspect the configuration

Read `main.tf` and any `variables.tf` or example backend file. Identify inputs, outputs, and the ownership boundary before executing Terraform.

```bash
cd ../labs/lab11-remote-state-consumer
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
terraform plan # after the upstream state file exists
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

## Design notes

Shared state is production-sensitive metadata. Treat its bucket, key naming, retention, encryption, and IAM policy as part of the platform design. A separate state key is an ownership boundary, not merely a filename. Review the planned state location before initialization and never solve a conflict by deleting locks or editing state without understanding the active operation.

For migration, make a backup and allow `terraform init -migrate-state` to copy state only after confirming the source and destination. For consumption, export narrow outputs from the producer and avoid using remote state as a broad inventory API.

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
*Deep dive: [docs/state/README.md](docs/state/README.md). Next: [Lab 12](lab12-collections.md)*

## Operational checklist

### Control 1 — Consumer contract

Expose only stable, intentionally public outputs from a producer root module.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 2 — Consumer contract

Treat output names and shapes as an interface with compatibility expectations.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 3 — Consumer contract

Avoid coupling a consumer to individual resource IDs when a higher-level output will do.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 4 — Consumer contract

Prefer a registry, service discovery, or data source when state is not the right integration boundary.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 5 — Consumer contract

Test a consumer after a producer output change before approving the producer release.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 6 — Consumer contract

Expose only stable, intentionally public outputs from a producer root module.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 7 — Consumer contract

Treat output names and shapes as an interface with compatibility expectations.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 8 — Consumer contract

Avoid coupling a consumer to individual resource IDs when a higher-level output will do.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 9 — Consumer contract

Prefer a registry, service discovery, or data source when state is not the right integration boundary.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 10 — Consumer contract

Test a consumer after a producer output change before approving the producer release.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```

### Control 11 — Consumer contract

Expose only stable, intentionally public outputs from a producer root module.

**Why it matters:** Terraform state and configuration are operational interfaces. A small convention made explicit before apply prevents accidental cross-environment changes later.

**Evidence to capture**

- The selected workspace and account identity.
- The reviewed plan summary and state location.
- The operator responsible for cleanup or rollback.

**Validate**

```bash
terraform workspace show
terraform state list
```

```text
The command output matches the intended environment and ownership boundary.
```
