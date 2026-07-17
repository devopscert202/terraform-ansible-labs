# 02 — Providers

## Overview

Providers are plugins that let Terraform manage external systems. Without a provider, Terraform can only manipulate its own internal graph — it cannot create an EC2 instance, a Kubernetes deployment, or a random string. Each provider implements resource types (e.g., `aws_instance`) and data sources (e.g., `aws_ami`) by calling the vendor's API.

For beginners, the provider layer is where **authentication** and **regional configuration** live. The AWS provider block sets `region`; credentials come from the environment. Understanding providers is prerequisite to every AWS lab in this track.

### Why this matters for beginners

Choosing the wrong provider version can break your configuration overnight when a major release changes attribute names. Pinning versions in `required_providers` and committing `.terraform.lock.hcl` prevents "works on my machine" drift. Knowing the difference between a **resource** (Terraform manages lifecycle) and a **data source** (read-only lookup) prevents accidental attempts to "create" an existing AMI ID.

---

## Key concepts

| Concept | Description | Lab reference |
|---------|-------------|---------------|
| `required_providers` | Declares which plugins are needed | Lab 01 `main.tf` |
| `source` | Registry address `hashicorp/aws` | All AWS labs |
| `version` constraint | Acceptable provider versions | `~> 5.0` |
| `provider` block | Configuration for a plugin instance | `region = "us-east-1"` |
| Provider alias | Multiple configs of same provider | Not used in essentials labs |
| `.terraform.lock.hcl` | Exact version + checksums after init | Created in Lab 01 |
| Data source | Read existing infrastructure | `data.aws_ami.ubuntu` in Lab 02 |

---

## Architecture: provider in the execution graph

```
┌─────────────────────────────────────────────────────────────┐
│                    terraform init                            │
│  Reads required_providers → downloads binaries → lock file   │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    terraform plan/apply                        │
│                                                              │
│   Configuration          Provider plugin        Cloud API    │
│   aws_instance.web  ──▶  hashicorp/aws 5.x  ──▶  EC2 API   │
│   random_pet.lab_id ──▶  hashicorp/random ──▶  (local)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-step: declare and use providers

### Lab 01 — Dual providers

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

Run:

```bash
cd terraform/essentials/labs/lab01-providers-init
terraform init
terraform providers
```

**Expected `terraform providers` output** includes:

```
├── provider[registry.terraform.io/hashicorp/aws] ~> 5.0
└── provider[registry.terraform.io/hashicorp/random] ~> 3.0
```

### Lab 02 — AWS provider with variables

```hcl
provider "aws" {
  region = var.aws_region
}
```

Default region is `us-east-1` from `variables.tf`. Override with:

```bash
export AWS_PROFILE=training
terraform plan -var="aws_region=us-west-2"
```

---

## Data sources vs resources (Lab 02)

**Data source** — lookup only; Terraform does not own the AMI:

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
```

**Resource** — Terraform creates and tracks the instance:

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
```

Reference syntax:

| Address | Type |
|---------|------|
| `data.aws_ami.ubuntu.id` | Data source attribute |
| `aws_instance.web.id` | Managed resource attribute |
| `var.instance_type` | Input variable |

---

## Version constraint reference

```hcl
version = "5.0.0"      # Exactly 5.0.0
version = ">= 5.0.0"   # 5.0.0 or newer
version = "~> 5.0"     # >= 5.0, < 6.0  ← used in this track
version = "~> 5.1"     # >= 5.1, < 6.0
```

After changing constraints:

```bash
terraform init -upgrade
```

---

## Inspecting installed providers

```bash
terraform version
# Shows Terraform CLI + selected provider versions

terraform providers
# Shows provider dependency tree

ls .terraform/providers/registry.terraform.io/hashicorp/aws/
# Provider binary on disk
```

---

## Authentication workflow

```bash
# 1. Set profile (never put keys in .tf)
export AWS_PROFILE=training

# 2. Verify before terraform commands
aws sts get-caller-identity

# 3. Run Terraform
cd terraform/essentials/labs/lab02-ec2
terraform init
terraform plan
```

The provider automatically picks up credentials from the profile. No `access_key` block is needed or permitted in this curriculum.

---

## Common mistakes

| Mistake | Symptom | Solution |
|---------|---------|----------|
| Missing `terraform init` after clone | `Could not load provider` | Run `init` |
| Wrong AWS region | Resources in unexpected region | Check `provider "aws" { region = ... }` |
| Hard-coded AMI ID | Breaks when AMI deprecated | Use `data.aws_ami` with filters |
| No version constraint | Surprise breaking upgrades | Always use `required_providers` |
| `access_key` in provider | Security violation | Remove; use `AWS_PROFILE` |
| Stale lock file after `-upgrade` | Team checksum mismatch | Commit updated `.terraform.lock.hcl` |

---

## Provider registry

Public providers: [registry.terraform.io](https://registry.terraform.io)

Common providers in enterprise environments:

| Provider | Source | Use case |
|----------|--------|----------|
| AWS | `hashicorp/aws` | EC2, VPC, S3, IAM |
| Random | `hashicorp/random` | Safe lab resources, passwords |
| Azure | `hashicorp/azurerm` | Azure RM resources |
| Google | `hashicorp/google` | GCP resources |

---

## Links

| Resource | Path |
|----------|------|
| Lab 01 | [labmanuals/lab01-providers-init.md](../../labmanuals/lab01-providers-init.md) |
| Lab 02 | [labmanuals/lab02-ec2.md](../../labmanuals/lab02-ec2.md) |
| Lab 02 files | [labs/lab02-ec2/](../../labs/lab02-ec2/) |
| HTML: Foundations | [html/foundations.html](../../html/foundations.html) |
| Previous | [01-getting-started/README.md](../01-getting-started/README.md) |
| Next | [03-resources/README.md](../03-resources/README.md) |

---

## Hands-on labs

1. **[Lab 01](../../labmanuals/lab01-providers-init.md)** — Install AWS + Random providers; run `terraform providers`.
2. **[Lab 02](../../labmanuals/lab02-ec2.md)** — Use AMI data source; deploy `aws_instance.web` with `AWS_PROFILE`.

---

## Key takeaways

1. Providers are **plugins** installed by `terraform init`, not built into the CLI.
2. Pin versions with `required_providers` and commit the **lock file**.
3. **Data sources** read; **resources** manage lifecycle.
4. AWS authentication uses the **credential chain** — configure `AWS_PROFILE`, not HCL secrets.
5. Lab 02 demonstrates the canonical pattern: **data source for AMI + resource for instance**.

---

## Next steps

Proceed to [03 — Resources](../03-resources/README.md) for resource addressing, dependencies, and outputs in depth.
