# Lab 14 — Dynamic blocks

> **Goal:** Generate nested `ingress` blocks on `aws_security_group` from a map using `dynamic` blocks.
> **Time:** ~35 min · **Directory:** `terraform/extended/labs/lab14-dynamic-blocks/`

## Learning objectives

After completing this lab you will be able to:

- Write `dynamic` blocks with `for_each` on maps
- Access iterator `.value` fields in nested schema
- Add/remove rules by editing map keys only
- Verify generated rules in AWS API/CLI
- Contrast dynamic blocks vs multiple static ingress stanzas

## Architecture

Dynamic blocks generate repeated nested `ingress` stanzas from a map variable.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.aws_region }

variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "ingress_rules" {
  type = map(object({ port = number, cidr_blocks = list(string), description = string }))
  default = {
    https = { port = 443, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTPS" }
    http  = { port = 80, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTP" }
  }
}

resource "aws_security_group" "service" {
  name_prefix = "extended-dynamic-"
  description = "Dynamic ingress demonstration"
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
output "security_group_id" { value = aws_security_group.service.id }
```

```text
var.ingress_rules ──dynamic ingress──► aws_security_group.service
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | dynamic ingress | Map-driven rules |
| 2 | apply | SG created |
| 3 | AWS CLI | Rules verified |
| 4 | Add ssh key | Third rule |
| 5 | destroy | Cleanup |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab14-dynamic-blocks
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Review ingress_rules variable

Map of port/cidr/description.

```bash
cd terraform/extended/labs/lab14-dynamic-blocks
grep -A8 'ingress_rules' main.tf
```

**Validate**

```text
Default https and http rules on 10.0.0.0/8.
```

### Step 2 — Study dynamic block

Iterator name `ingress` exposes `.value`.

```bash
grep -A12 'dynamic "ingress"' main.tf
```

**Validate**

```text
for_each over map; content block populated.
```

### Step 3 — Verify AWS credentials

Creates real security group.

```bash
aws sts get-caller-identity
export AWS_PROFILE=your-training-profile
```

**Validate**

```text
Account identified.
```

### Step 4 — Initialize and validate

AWS provider required.

```bash
terraform init
terraform validate
```

**Validate**

```text
Valid.
```

### Step 5 — Plan

One security group with two ingress rules.

```bash
terraform plan
```

**Validate**

```text
aws_security_group.service to be created.
```

### Step 6 — Apply

SG created in your account.

```bash
terraform apply -auto-approve
```

**Validate**

```text
security_group_id output.
```

### Step 7 — AWS console verification

Compare dynamic rules to console.

```bash
aws ec2 describe-security-groups --group-ids $(terraform output -raw security_group_id)
```

**Validate**

```text
Two ingress rules matching map.
```

### Step 8 — Add rule via variable

Extend map without editing HCL structure.

```bash
terraform apply -auto-approve -var='ingress_rules={https={port=443,cidr_blocks=["10.0.0.0/8"],description="internal HTTPS"},http={port=80,cidr_blocks=["10.0.0.0/8"],description="internal HTTP"},ssh={port=22,cidr_blocks=["10.0.0.0/8"],description="bastion SSH"}}'
```

**Validate**

```text
Third ingress appears in plan/apply.
```

### Step 9 — Remove rule

Omitting map key removes block.

```bash
terraform apply -auto-approve
```

**Validate**

```text
Plan shows ingress rule removal.
```

### Step 10 — Destroy

Cleanup SG before leaving.

```bash
terraform destroy -auto-approve
```

**Validate**

```text
SG deleted.
```

## Design notes

Dynamic blocks reduce duplication but hide structure in plans — review carefully. They apply to nested blocks, not resources. Empty `for_each` yields zero blocks (valid). For complex rule sets, consider `aws_vpc_security_group_ingress_rule` (Terraform 1.5+ style) in new designs.

## Done when

- [ ] Created SG with dynamic ingress
- [ ] Added rule via map extension
- [ ] Verified rules via AWS CLI

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| SG already exists | name_prefix collision | Import or taint |
| Rule not visible | Wrong account/region | Check AWS_PROFILE |

## Cleanup

```bash
terraform destroy -auto-approve  # if not already
rm -rf .terraform terraform.tfstate*
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/functions/README.md](../docs/functions/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/functions/README.md](../docs/functions/README.md) · Next: [Lab 15 — Capstone projects](lab15-capstone-projects.md)*

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

## Reference — ownership questions (continued 2)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts (continued 2)


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab (continued 2)


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links (continued 2)


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |
