# Terraform Project Layout and Capstone Patterns

## Objective (conceptual)

A **Terraform project** is more than one `.tf` file—it is how you organize roots, backends, workspaces, variables, and modules for multiple environments. Capstone labs combine VPC networking, tagged resources, and workspace-aware naming so `dev` and `staging` never share the same logical name in AWS.

The mental model: essentials taught **one directory = one stack**; extended projects teach **one repository = many stacks** with remote state, conventions, and reviewable promotion from dev to prod.

**Interactive reference:** [Projects](../../html/projects.html)

## Capstone root pattern (Lab 15)

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name = "${var.project}-${terraform.workspace}"
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = local.name })
}

resource "aws_subnet" "public" {
  for_each                = var.public_subnets
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true
  tags                    = merge(var.tags, { Name = "${local.name}-${each.key}" })
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = { for name, subnet in aws_subnet.public : name => subnet.id }
}
```

- `terraform.workspace` suffixes names per environment.
- `for_each` on `public_subnets` scales AZ coverage without duplication.
- `merge(var.tags, ...)` keeps org-wide tags consistent.

## Recommended repository layout

```
terraform/extended/labs/lab15-capstone-projects/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars.example
└── backend.hcl.example   # supplied at init, not committed with secrets
```

Separate **code** (git) from **secrets** (CI variables, Vault) and **state** (S3).

## Multi-provider composition (Lab 03)

Extended roots may register multiple providers in one configuration:

```hcl
terraform {
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "random" {}

resource "random_pet" "label" {
  length = 2
}

output "provider_composition" {
  value = {
    aws_region        = var.aws_region
    generated_label   = random_pet.label.id
  }
}
```

Use one provider block per cloud; alias when multi-region.

## Environment promotion workflow

1. **Dev** — workspace or `dev` state key; liberal destroy/recreate.
2. **Staging** — plan-only CI on PR; apply on merge with approval.
3. **Prod** — locked module versions, peer review, drift detection scheduled.

## Project hygiene checklist

- [ ] Remote backend + locking enabled
- [ ] `terraform.tfvars.example` documents required variables
- [ ] No credentials in VCS; `AWS_PROFILE` or OIDC in CI
- [ ] Module and provider versions pinned
- [ ] README lists how to `init` with backend config
- [ ] `destroy` documented for cost control

## Console VPC lab (Lab 01)

`lab01-console-vpc` README documents importing or mirroring console-built networking into Terraform—a bridge exercise before full code-first capstones.

## Operational commands (reference)

```bash
cd terraform/extended/labs/lab15-capstone-projects
terraform init -backend-config=backend.hcl.example
terraform workspace select dev || terraform workspace new dev
terraform plan -var-file=terraform.tfvars.example
terraform apply

cd ../lab03-multi-cloud-providers
terraform init
terraform plan
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 01: Console VPC](../../labmanuals/lab01-console-vpc.md) | Align console-created VPC with Terraform patterns |
| [Lab 03: Multi-Cloud Providers](../../labmanuals/lab03-multi-cloud-providers.md) | Multiple providers in one root module |
| [Lab 15: Capstone Projects](../../labmanuals/lab15-capstone-projects.md) | VPC, subnets, workspaces, tagging |
