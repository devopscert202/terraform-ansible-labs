# 03 — Resources

## Overview

Resources are the heart of Terraform configuration. A `resource` block declares an infrastructure object that Terraform **creates, updates, and destroys** to match your specification. When you run `terraform apply`, the provider calls cloud APIs on your behalf; when you run `terraform destroy`, Terraform removes objects it still tracks in state.

This chapter covers resource addressing, implicit dependencies, tags, outputs, and the EC2 patterns used in Labs 02 and 05. Understanding resources is essential before learning workflow commands (plan/apply) in the next chapter.

### Why this matters for beginners

Every `terraform plan` line like `+ aws_instance.web` refers to a **resource address**. Beginners who confuse resources with data sources often try to `terraform destroy` an AMI lookup or wonder why a data block never appears as `+ create`. Resources also carry **metadata** (tags, names) that organizations use for cost allocation and ownership — Labs 02 and 05 teach tagging conventions.

---

## Key concepts

| Concept | Description | Example |
|---------|-------------|---------|
| Resource type | Provider-specific object kind | `aws_instance` |
| Resource name | Local label in your config | `web` in `aws_instance.web` |
| Address | Type + name | `aws_instance.web` |
| Attribute | Exported property after create | `aws_instance.web.public_ip` |
| Implicit dependency | Reference creates ordering | Subnet references VPC id |
| Tags | Key-value metadata on AWS objects | `ManagedBy = "Terraform"` |
| Output | Exposes resource attributes post-apply | `output "instance_id"` |

---

## Resource lifecycle (ASCII)

```
  .tf configuration          terraform apply              Real infrastructure
 ┌─────────────────┐        ┌───────────────┐           ┌─────────────────┐
 │ aws_instance    │  ───▶  │ Provider API  │  ───▶     │ EC2 i-0abc123   │
 │   "web" { ... } │        │ CreateInstance│           │ running         │
 └─────────────────┘        └───────┬───────┘           └─────────────────┘
                                     │
                                     ▼
                            terraform.tfstate
                            stores id, arn, ip...
```

---

## Lab 02 — EC2 resource anatomy

File: `labs/lab02-ec2/main.tf`

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  tags = {
    Name      = var.instance_name
    ManagedBy = "Terraform"
    Lab       = "terraform-essentials-lab02"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}

output "public_ip" {
  value = aws_instance.web.public_ip
}
```

Variables (`variables.tf`):

```hcl
variable "aws_region" {
  description = "AWS region for the instance."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance."
  type        = string
  default     = "terraform-essentials-web"
}
```

---

## Step-by-step: deploy Lab 02

```bash
export AWS_PROFILE=training
aws sts get-caller-identity

cd terraform/essentials/labs/lab02-ec2
terraform init
terraform validate
terraform plan
```

**Plan expectation:** `1 to add` — `aws_instance.web`

```bash
terraform apply
```

Type `yes`. Note outputs:

```
instance_id = "i-0xxxxxxxxxxxx"
public_ip   = "x.x.x.x"   # may be empty if no public IP assigned
```

```bash
terraform destroy
```

---

## Lab 05 — Locals and merged tags

File: `labs/lab05-variables/main.tf`

```hcl
locals {
  common_tags = merge(var.tags, {
    Name      = var.server_name
    Service   = "terraform-essentials"
    ManagedBy = "Terraform"
  })
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  tags          = local.common_tags
}
```

The `merge()` function combines maps. Keys in the second map override the first on collision.

---

## Implicit vs explicit dependencies

**Implicit** (preferred) — attribute reference:

```hcl
resource "aws_subnet" "this" {
  vpc_id = aws_vpc.this.id   # subnet waits for VPC
}
```

**Explicit** — `depends_on` when no attribute reference exists:

```hcl
resource "aws_instance" "web" {
  depends_on = [aws_iam_role_policy_attachment.example]
}
```

Lab 07's subnet → VPC relationship uses implicit dependency via `vpc_id`.

---

## Resource addressing reference

```
resource "TYPE" "NAME" { }

Examples:
  aws_instance.web           → managed EC2 instance named "web"
  random_pet.lab_id          → random pet named "lab_id"
  module.network.aws_vpc.this → resource inside child module
```

In plans:

```
+ create   aws_instance.web
~ update   aws_instance.web
- destroy  aws_instance.web
```

---

## Outputs as contract

Root module outputs are the **public API** after apply:

```hcl
output "instance_arn" {
  value = aws_instance.web.arn
}
```

Retrieve without re-applying:

```bash
terraform output instance_id
terraform output -json
```

Lab 04 marks an output `sensitive = true` — CLI redacts the value in normal output.

---

## Random provider resources (no AWS cost)

Lab 03 uses a lightweight resource for workflow practice:

```hcl
resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}
```

Same resource semantics: Terraform owns the object in state.

---

## Common mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| Wrong resource type name | Validate error | Check provider docs for exact type |
| Missing required argument | Plan/apply error | e.g., `ami` required on `aws_instance` |
| Duplicate resource name | Config error | Each TYPE+NAME pair must be unique |
| Changing `name` label | Destroy + recreate | Use `terraform state mv` if refactoring |
| Forgetting tags | Hard to identify resources | Always tag with Name, ManagedBy |
| No `destroy` after lab | AWS charges continue | Run `terraform destroy` |

---

## Tagging standards (this track)

| Tag | Purpose | Labs |
|-----|---------|------|
| `Name` | Human-readable identifier | 02, 05, 07 |
| `ManagedBy` | Shows Terraform ownership | 02, 05, 07 |
| `Lab` | Training exercise ID | 02 |
| `Environment` | From `var.tags` map | 05 |
| `Owner` | Team ownership | 05 |

---

## Links

| Resource | Path |
|----------|------|
| Lab 02 manual | [labmanuals/lab02-ec2.md](../../labmanuals/lab02-ec2.md) |
| Lab 05 manual | [labmanuals/lab05-variables.md](../../labmanuals/lab05-variables.md) |
| HTML: Foundations | [html/foundations.html](../../html/foundations.html) |
| Previous | [02-providers/README.md](../02-providers/README.md) |
| Next | [04-workflow/README.md](../04-workflow/README.md) |

---

## Hands-on labs

| Lab | Resource focus |
|-----|----------------|
| [Lab 02](../../labmanuals/lab02-ec2.md) | `aws_instance.web` with AMI data source |
| [Lab 03](../../labmanuals/lab03-plan-apply-destroy.md) | `random_string.example` lifecycle |
| [Lab 05](../../labmanuals/lab05-variables.md) | Tagged EC2 with `locals` |

---

## Key takeaways

1. **Resources** are managed objects; **data sources** are read-only lookups.
2. Resource **addresses** (`aws_instance.web`) appear in plans, state, and CLI.
3. **Implicit dependencies** via attribute references control create order.
4. **Outputs** expose IDs and IPs for verification and automation.
5. Always **tag** and **destroy** AWS resources after labs.

---

## Next steps

Read [04 — Workflow](../04-workflow/README.md) for init/plan/apply/destroy in detail.
