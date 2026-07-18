# Terraform Providers

## Objective (conceptual)

Providers are plugins that connect Terraform to external systems. Without a provider, Terraform can only reason about its own graph—it cannot create an EC2 instance, read an AMI, or generate a random string. The provider layer is where **regional settings** and **authentication context** live for each API.

Pinning provider versions in `required_providers` and committing `.terraform.lock.hcl` prevents surprise breakage when a major release changes attribute names. Knowing the difference between a **resource** (Terraform manages lifecycle) and a **data source** (read-only lookup) keeps you from trying to "create" something that already exists in the cloud.

**Interactive reference:** [Foundations](../../html/foundations.html)

## Declaring providers

- `required_providers` — Declares which plugins `init` must download.
- `source` — Registry address, e.g. `hashicorp/aws`.
- `version` — Constraint such as `~> 5.0` (5.x only).
- `provider` block — Runtime config (typically `region` for AWS).
- `.terraform.lock.hcl` — Exact version and checksums after `init`.

## Dual providers in Lab 01

Lab 01 registers AWS and Random providers. Only `random_pet` is created on apply—AWS is declared so later labs share the same pattern.

```hcl
terraform {
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

## Data sources vs resources (Lab 02)

A **data source** looks up existing infrastructure. Lab 02 resolves the latest Ubuntu 22.04 AMI instead of hard-coding an AMI ID that differs per region.

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

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  # ...
}
```

- `data.aws_ami.ubuntu` — Read at plan/apply time; not stored as a managed resource.
- `aws_instance.web` — Terraform creates, updates, and destroys this object.

## Provider execution graph

```
terraform init  →  download hashicorp/aws, hashicorp/random  →  lock file
terraform plan  →  config blocks  →  provider plugins  →  cloud APIs
```

## Version constraint cheat sheet

| Syntax | Accepts |
|--------|---------|
| `>= 5.0` | 5.0 and any newer major |
| `~> 5.0` | ≥ 5.0, &lt; 6.0 |
| `= 5.100.0` | Exactly one version (rare in apps) |

## Authentication rules

- Set `region` in the `provider "aws"` block.
- Use `AWS_PROFILE`, environment variables, or IAM roles—never `access_key` / `secret_key` in `.tf` files.
- Random provider needs no cloud credentials.

## Provider aliases (concept)

Multiple `provider "aws"` blocks with `alias` let one configuration target two regions. Essentials labs use a single default provider; extended multi-cloud labs introduce additional patterns.

## Upgrading providers

When `required_providers` version constraints change:

```bash
terraform init -upgrade
terraform plan    # review provider-driven diffs carefully
```

Major provider bumps may require `terraform state replace-provider`—rare in essentials labs but common in production maintenance windows.

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab01-providers-init
terraform init          # download providers
terraform providers     # show resolved provider versions
terraform version

cd ../lab02-ec2
terraform init
terraform plan
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 01: Providers and Init](../../labmanuals/lab01-providers-init.md) | Declare providers, run `init`, inspect lock file |
| [Lab 02: EC2 Instance](../../labmanuals/lab02-ec2.md) | AWS provider, AMI data source, security group, instance |
