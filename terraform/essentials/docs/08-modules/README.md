# Terraform Modules

## Objective (conceptual)

A **module** is a container of Terraform configuration with its own inputs and outputs. The **root module** is the directory where you run `terraform apply`; **child modules** are reusable packages called via `module` blocks. Modules let teams share VPC patterns, tagging standards, and naming conventions without copy-pasting `.tf` files.

The mental model: the root module is the **composer**; child modules are **libraries**. Data flows in through `variables`, out through `outputs`, and resources inside the child stay encapsulated unless exported.

**Interactive reference:** [Modules](../../html/modules.html)

## Calling a child module (Lab 07)

Root `main.tf` invokes `./modules/network`:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source      = "./modules/network"
  name        = var.name
  vpc_cidr    = var.vpc_cidr
  subnet_cidr = var.subnet_cidr
}

output "vpc_id" {
  value = module.network.vpc_id
}

output "subnet_id" {
  value = module.network.subnet_id
}
```

## Child module resources

`modules/network/main.tf`:

```hcl
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = {
    Name      = "${var.name}-vpc"
    ManagedBy = "Terraform"
  }
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.subnet_cidr

  tags = {
    Name      = "${var.name}-subnet"
    ManagedBy = "Terraform"
  }
}
```

Child modules declare their own `variable` and `output` blocks in sibling files (`variables.tf`, `outputs.tf`).

## Module addressing in state

State paths include the module call:

- `module.network.aws_vpc.this`
- `module.network.aws_subnet.this`

References from root use `module.network.vpc_id`, not direct resource addresses inside the child.

## When to extract a module

- The same VPC + subnet pattern repeats across projects.
- You need versioned releases (`source = "git::..."` or Terraform Registry).
- Blast radius: network team owns the module; app teams consume outputs only.

## Module sources (reference)

| Source | Example |
|--------|---------|
| Local path | `source = "./modules/network"` |
| Registry | `source = "terraform-aws-modules/vpc/aws"` |
| Git | `source = "git::https://example.com/repo.git//modules/vpc"` |

Essentials uses local paths only.

## Inputs, outputs, and secrets

- Pass **non-secret** sizing and naming via module variables.
- Never pass static credentials into modules—use provider configuration and IAM.
- Export only what consumers need (`vpc_id`, `subnet_id`)—not every internal resource.

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab07-simple-module
terraform init    # installs providers for root and child
terraform plan
terraform apply
terraform state list | grep module.network
terraform destroy
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 07: Simple Module](../../labmanuals/lab07-simple-module.md) | Local child module, pass variables, read outputs |
| [Extended Lab 15: Capstone Projects](../../../extended/labmanuals/lab15-capstone-projects.md) | Multi-resource root module with workspaces |
