# 08 — Modules

## Overview

Modules are containers for multiple resources that are used together. A **root module** is the directory where you run Terraform commands; **child modules** are called via `module` blocks. Modules have their own variables (inputs) and outputs, forming a contract between platform and consumer.

Lab 07 extracts VPC + subnet into `./modules/network`. This is the pattern platform teams use to publish blessed building blocks. Lab 08 (tfvars/secrets) complements modules by showing how root modules accept validated, sensitive inputs.

### Why this matters for beginners

Without modules, copy-paste spreads errors across environments. With modules, you fix a subnet bug once in `modules/network` and every caller benefits. Understanding `module.network.vpc_id` syntax is required for reading any production Terraform repository.

---

## Key concepts

| Concept | Description | Lab 07 |
|---------|-------------|--------|
| Root module | Working directory with `terraform apply` | `lab07-simple-module/` |
| Child module | Called via `module` block | `modules/network/` |
| `source` | Module location | `"./modules/network"` |
| Module input | Variable in child | `vpc_cidr` |
| Module output | Exported value | `vpc_id` |
| Module address | In state | `module.network.aws_vpc.this` |

---

## Module hierarchy (Lab 07)

```
lab07-simple-module/          ← ROOT MODULE
├── main.tf                   ← module "network" { ... }
├── variables.tf
└── modules/
    └── network/              ← CHILD MODULE
        ├── main.tf           ← aws_vpc, aws_subnet
        ├── variables.tf
        └── outputs.tf
```

---

## Root module — main.tf

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

### Root variables.tf

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  type    = string
  default = "terraform-essentials"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "subnet_cidr" {
  type    = string
  default = "10.42.1.0/24"
}
```

---

## Child module — modules/network/main.tf

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

### Child variables.tf

```hcl
variable "name" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "subnet_cidr" {
  type = string
}
```

### Child outputs.tf

```hcl
output "vpc_id" {
  value = aws_vpc.this.id
}

output "subnet_id" {
  value = aws_subnet.this.id
}
```

---

## Deploy Lab 07

```bash
export AWS_PROFILE=training
aws sts get-caller-identity

cd terraform/essentials/labs/lab07-simple-module
terraform init
terraform validate
terraform plan
```

Expected: `2 to add` — `module.network.aws_vpc.this`, `module.network.aws_subnet.this`

```bash
terraform apply
terraform output vpc_id
terraform output subnet_id
terraform destroy
```

---

## Module sources

| Source type | Example |
|-------------|---------|
| Local path | `source = "./modules/network"` |
| Registry | `source = "terraform-aws-modules/vpc/aws"` |
| Git | `source = "git::https://github.com/org/repo.git//modules/vpc"` |
| S3 | `source = "s3::https://s3.amazonaws.com/bucket/modules/vpc.zip"` |

Lab 07 uses local path — simplest for learning.

### Registry example (reference)

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["us-east-1a", "us-east-1b"]
}
```

---

## init and modules

```bash
terraform init
```

Downloads providers **and** installs modules to `.terraform/modules/`. After adding a new `module` block, always re-run `init`.

```bash
cat .terraform/modules/modules.json
```

---

## Data flow between modules

```
Root variables  ──▶  module inputs  ──▶  child resources
                                              │
Child outputs   ◀──  module outputs ◀─────────┘
       │
       ▼
Root outputs (vpc_id, subnet_id)
```

**Rule:** Modules communicate only through **inputs** and **outputs**. Do not reference `module.other.aws_vpc.this` from a sibling module — pass via root.

---

## When to create a module

Create a module when:

- The same resource group appears in 2+ environments
- You want independent `terraform validate` on a component
- A platform team publishes standard building blocks
- File count and complexity exceed ~50 lines with clear boundaries

Keep inline when:

- Single one-off resource (Labs 01–03)
- Learning basic syntax

---

## Lab 08 — Root module inputs (complement)

Lab 08 has no child modules but demonstrates **root module variable validation** and **sensitive** inputs — skills needed when **calling** modules with strict contracts.

```hcl
variable "phone_number" {
  type        = string
  description = "Pass via TF_VAR_phone_number"
  sensitive   = true
}
```

---

## Common mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| Forgot `init` after new module | Module not installed | `terraform init` |
| Cross-module resource reference | Tight coupling | Use outputs → inputs via root |
| No outputs on module | Can't wire downstream | Export IDs, ARNs |
| Hard-coded values in child | Inflexible module | Expose as variables |
| Wrong relative path | Init failure | Verify `source = "./modules/..."` |
| Apply child module directory alone | Missing provider | Apply from root only |

---

## Links

| Resource | Path |
|----------|------|
| Lab 07 | [labmanuals/lab07-simple-module.md](../../labmanuals/lab07-simple-module.md) |
| Lab 08 | [labmanuals/lab08-tfvars-secrets.md](../../labmanuals/lab08-tfvars-secrets.md) |
| HTML: Modules | [html/modules.html](../../html/modules.html) |
| Previous | [07-state/README.md](../07-state/README.md) |
| Index | [01-getting-started/README.md](../01-getting-started/README.md) |

---

## Hands-on labs

1. **[Lab 07](../../labmanuals/lab07-simple-module.md)** — VPC + subnet child module.
2. **[Lab 08](../../labmanuals/lab08-tfvars-secrets.md)** — Validation and secrets at root module.

---

## Key takeaways

1. **Root module** runs apply; **child modules** encapsulate resources.
2. Interface = **variables in**, **outputs out**.
3. `module.network.vpc_id` references child output from root.
4. Run **`terraform init`** when `source` changes.
5. Lab 07 creates real VPC resources — **destroy** when done.

---

## Curriculum complete

You have covered providers, resources, workflow, quality, variables, state, and modules. Return to [html/index.html](../../html/index.html) for the full track map.
