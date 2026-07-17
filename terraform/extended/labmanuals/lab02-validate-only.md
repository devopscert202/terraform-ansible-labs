# Lab 02 — Validate-only

> **Goal:** Practice init and validate workflow without creating cloud infrastructure.
> **Time:** ~30 min · **Directory:** `terraform/extended/labs/lab02-validate-only/`

## Learning objectives

After completing this lab you will be able to:

- Run `terraform init` and `terraform validate` successfully
- Explain what `terraform_data` represents
- Read outputs from a minimal root module
- Establish fmt/validate habits before every plan

## Architecture

```hcl
# main.tf — no cloud providers
resource "terraform_data" "validation_probe" {
  input = local.course
}
```

State is local `terraform.tfstate` containing only the `terraform_data` address.

## Exercise index

| # | Exercise | Command |
|---|----------|----------|
| 1 | Inspect config | `cat main.tf` |
| 2 | Initialize | `terraform init` |
| 3 | Validate | `terraform validate` |
| 4 | Plan/apply | `terraform apply` |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab02-validate-only
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Inspect configuration

Read `main.tf` — note `required_version` and `terraform_data`.

```bash
cd terraform/extended/labs/lab02-validate-only
cat main.tf
```

**Validate**

```text
You see `terraform_data.validation_probe` and output `validation_probe`.
```

### Step 2 — Format check

Terraform fmt ensures canonical style.

```bash
terraform fmt -check
terraform fmt
```

**Validate**

```text
fmt reports no differences (or fixes applied).
```

### Step 3 — Initialize

Downloads providers (none beyond built-in) and prepares backend.

```bash
terraform init
```

**Validate**

```text
Success message; `.terraform/` directory created.
```

### Step 4 — Validate

Static analysis of types and references.

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

### Step 5 — Plan and apply

Apply is safe — only `terraform_data` changes.

```bash
terraform plan
terraform apply
```

**Validate**

```text
Apply complete; output `validation_probe` = `terraform-extended`.
```

### Step 6 — State inspection

Practice read-only state commands.

```bash
terraform state list
terraform state show terraform_data.validation_probe
```

**Validate**

```text
State address listed with input attribute visible.
```



## Terraform workflow deep dive

### Step 7 — Understand terraform_data

`terraform_data` is a resource that stores arbitrary metadata in state without calling a cloud API.

```bash
terraform console
```

```
> terraform_data.validation_probe.input
(local.course value after apply — read main.tf for local.course)
```

Type `exit` to leave the console.

**Validate**

```text
Console loads without error after terraform init.
```

### Step 8 — Plan file optional practice

```bash
terraform plan -out=lab02.tfplan
terraform show lab02.tfplan
```

**Validate**

```text
Plan shows 0 to add/change/destroy after initial apply, or 1 add on first run.
```

### Step 9 — Version constraints

```bash
grep required_version main.tf
```

**Validate**

```text
required_version = ">= 1.5.0" is present — matches course requirement.
```

### Step 10 — Lock file inspection

After init, inspect provider lock file (may be empty of providers for this lab):

```bash
ls -la .terraform.lock.hcl 2>/dev/null || echo "No providers to lock"
cat .terraform/terraform.tfstate 2>/dev/null | head -5
```

**Validate**

```text
You understand init creates .terraform/ metadata directory.
```

## Design notes

Validation-first workflows catch errors before any cloud API call. Teams often enforce:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

in CI for every pull request. Lab 02 is the template for that gate.

### State file anatomy

After apply, open `terraform.tfstate` (training only — never commit):

```json
{
  "resources": [
    {
      "type": "terraform_data",
      "name": "validation_probe",
      ...
    }
  ]
}
```

### Reflection questions

1. What is the difference between `terraform plan` and `terraform apply`?
2. Why should state files be excluded from git?
3. What would happen if you deleted state but left the resource in code?

## Command reference

| Command | Purpose |
|---------|---------|
| `terraform fmt` | Canonical formatting |
| `terraform init` | Install providers, configure backend |
| `terraform validate` | Static type/syntax check |
| `terraform plan` | Propose changes |
| `terraform apply` | Execute changes |
| `terraform destroy` | Remove managed resources |
| `terraform state list` | List addresses in state |

## Extended exercises

| # | Task | Hint |
|---|------|------|
| E1 | Change `local.course` and re-apply | Observe update in place |
| E2 | Add invalid reference `var.does_not_exist` | validate should fail |
| E3 | Run `terraform providers` | See provider requirements |


## Done when

- [ ] Ran init, validate, plan, apply
- [ ] Explained why no AWS resources were created
- [ ] Captured output value




## Troubleshooting (validate)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `terraform: command not found` | Not in PATH | Install Terraform 1.5+ |
| `Module not installed` | Skipped init | Run `terraform init` |
| `Invalid reference` | Typo in config | Read error line number |
| State locked | Another process | Wait or identify holder |

## CI template snippet

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform fmt -check -recursive
      - run: terraform init -backend=false
      - run: terraform validate
```


## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |


## Cleanup

```bash
rm -rf .terraform terraform.tfstate terraform.tfstate.backup
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.



---
*Deep dive: [docs/projects/README.md](../docs/projects/README.md) · Next: [Lab 03 — Multi-cloud providers](lab03-multi-cloud-providers.md)*
