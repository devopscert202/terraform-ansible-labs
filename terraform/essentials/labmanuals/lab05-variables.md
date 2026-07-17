# Lab 05 — Variables, Locals, and Tags

> **Goal:** Deploy an EC2 instance whose region, name, instance type, and tags are driven entirely by variables and merged locals.
> **Time:** ~60 min · **Difficulty:** Beginner · **Files:** `labs/lab05-variables/`

## Overview

Hardcoded infrastructure does not survive multiple environments. This lab uses `variables.tf` for inputs, `locals` to merge tag maps, and `terraform.tfvars` for environment-specific values. You provision `aws_instance.web` with a data-sourced Ubuntu AMI — the same pattern as Lab 02, now parameterized.

## Learning objectives

- Declare typed variables with defaults and descriptions
- Use `locals` and `merge()` for computed tag maps
- Load values from `terraform.tfvars`
- Override variables with `TF_VAR_` environment variables
- Read `instance_arn` output after apply
- Destroy the instance when finished

## Prerequisites

- [ ] Terraform 1.5+ and AWS CLI configured
- [ ] `export AWS_PROFILE=training` (or EC2 instance profile)
- [ ] Lab 02 complete (EC2 basics)
- [ ] Working directory: `terraform/essentials/labs/lab05-variables`

## What you will build

```
terraform/essentials/labs/lab05-variables/
├── main.tf          # provider, data source, locals, aws_instance
├── variables.tf     # aws_region, server_name, instance_type, tags
└── outputs.tf       # instance_arn
```

---

## Exercise 1 — Authenticate and navigate

<a id="ex1"></a>

### Step 1.1 — Set AWS profile

```bash
export AWS_PROFILE=training
aws sts get-caller-identity
```

**Validate** — JSON with Account and Arn.

**What happened:** Provider uses credential chain — no keys in `.tf` files.

### Step 1.2 — Enter lab directory

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab05-variables
ls -la
```

**Validate** — `main.tf`, `variables.tf`, `outputs.tf` present.

---

## Exercise 2 — Study variables.tf

<a id="ex2"></a>

### Step 2.1 — Review variable declarations

```bash
cat variables.tf
```

**Validate** — four variables:

| Variable | Type | Default |
|----------|------|---------|
| `aws_region` | string | `us-east-1` |
| `server_name` | string | `variables-lab-web` |
| `instance_type` | string | `t3.micro` |
| `tags` | map(string) | Environment, Owner |

**What happened:** Defaults let you plan without tfvars; production modules often omit defaults for required inputs.

### Step 2.2 — Review locals in main.tf

```bash
grep -A8 'locals {' main.tf
```

**Validate** — `common_tags` merges `var.tags` with Name, Service, ManagedBy.

**What happened:** `merge()` combines maps; later keys override earlier keys on collision.

---

## Exercise 3 — Create terraform.tfvars

<a id="ex3"></a>

### Step 3.1 — Create tfvars file

```bash
cat > terraform.tfvars << 'EOF'
aws_region    = "us-east-1"
server_name   = "lab05-my-web"
instance_type = "t3.micro"

tags = {
  Environment = "training"
  Owner       = "student"
}
EOF
```

**Validate**

```bash
grep server_name terraform.tfvars
```

**What happened:** `terraform.tfvars` auto-loads on plan/apply. Add to `.gitignore` if not already.

---

## Exercise 4 — Init, fmt, validate

<a id="ex4"></a>

### Step 4.1 — Initialize

```bash
terraform init
```

**Validate** — successfully initialized.

### Step 4.2 — Format and validate

```bash
terraform fmt -recursive
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

---

## Exercise 5 — Plan with variables

<a id="ex5"></a>

### Step 5.1 — Plan

```bash
terraform plan
```

**Validate** — plan shows:

- `+ aws_instance.web`
- `instance_type = "t3.micro"` (from tfvars)
- Tags include `Name = "lab05-my-web"` from merged locals

**What happened:** Terraform resolved variables before computing the graph.

### Step 5.2 — Override with -var

```bash
terraform plan -var="instance_type=t3.small"
```

**Validate** — plan shows `t3.small` instead of `t3.micro`.

**What happened:** CLI `-var` overrides tfvars. Do not apply this unless you intend the larger size.

---

## Exercise 6 — TF_VAR environment override

<a id="ex6"></a>

### Step 6.1 — Export TF_VAR

```bash
export TF_VAR_server_name="env-override-web"
terraform plan | grep -A2 'tags'
```

**Validate** — Name tag reflects `env-override-web`.

```bash
unset TF_VAR_server_name
```

**What happened:** `TF_VAR_<name>` sets variables without editing files — useful in CI.

---

## Exercise 7 — Apply and verify

<a id="ex7"></a>

### Step 7.1 — Apply

```bash
terraform apply
```

Type `yes` when plan matches expectations (t3.micro from tfvars).

**Validate**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

### Step 7.2 — Read output

```bash
terraform output instance_arn
```

**Validate** — ARN like `arn:aws:ec2:us-east-1:ACCOUNT:instance/i-...`

### Step 7.3 — Verify tags in AWS

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=lab05-my-web" \
  --query 'Reservations[0].Instances[0].Tags' \
  --output table
```

**Validate** — tags include Service=`terraform-essentials`, ManagedBy=`Terraform`.

**What happened:** Locals applied consistent platform tags across resources.

---

## Exercise 8 — Change variable and update

<a id="ex8"></a>

### Step 8.1 — Edit server_name in tfvars

```bash
sed -i.bak 's/lab05-my-web/lab05-renamed-web/' terraform.tfvars
terraform plan
```

**Validate** — plan shows `~ tags` update (Name change), not full replacement.

### Step 8.2 — Apply tag change

```bash
terraform apply
```

**Validate** — apply completes with 0 added, 1 changed (or similar).

**What happened:** Tag updates are in-place for EC2 instances.

---

## Exercise 9 — Destroy

<a id="ex9"></a>

### Step 9.1 — Destroy instance

```bash
terraform destroy
```

**Validate** — destroy complete; state empty.

### Step 9.2 — Cleanup

```bash
rm -f terraform.tfvars terraform.tfvars.bak
```

**What happened:** Remove local tfvars if they contain personal identifiers.

---

## Key takeaways

- Variables parameterize modules; tfvars hold environment values
- Locals compute derived values without new inputs
- `merge()` builds tag maps from platform + resource tags
- `TF_VAR_` and `-var` override tfvars for testing
- Never commit secrets in tfvars

## Done when

- [ ] Applied with custom `terraform.tfvars`
- [ ] Verified merged tags in AWS console or CLI
- [ ] Demonstrated `-var` or `TF_VAR_` override in plan
- [ ] Read `instance_arn` output
- [ ] Destroyed instance

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| No valid credentials | AWS_PROFILE | Export profile |
| Wrong instance type in plan | TF_VAR left set | `unset TF_VAR_*` |
| UnauthorizedOperation | IAM | Request EC2 permissions |
| Invalid type for tags | tfvars syntax | Use map `{ key = "value" }` |

## Cleanup

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab05-variables
terraform destroy -auto-approve 2>/dev/null || true
rm -f terraform.tfvars terraform.tfstate.backup
```

## Next steps

- [Lab 06 — Local state](lab06-local-state.md)
- [Variables doc](../docs/06-variables/README.md)
- [Variables HTML](../html/variables.html)

---
*Terraform Essentials · Next: [lab06](lab06-local-state.md)*
