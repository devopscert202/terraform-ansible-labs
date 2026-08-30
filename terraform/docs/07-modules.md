# Terraform Modules

Backs lab 09. Covers what a module actually is, the boundary between root and child, how values
cross that boundary, how module resources are addressed in state, and when extracting a module is
worth it.

## Every configuration is already a module

A **module** is nothing more exotic than a directory containing `.tf` files. You have been writing
modules since lab01 without the word being used.

What changes in lab09 is that one module calls another:

- The **root module** is the directory you run `terraform apply` in. It is where state lives and
  where the backend and provider are configured.
- A **child module** is a directory called from somewhere else via a `module` block. It has its own
  variables and outputs, and no state of its own.

The relationship is a function call. The root passes arguments in, the child does work, the child
returns values out. Everything else inside the child is private.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Lab09's layout

```
terraform/labs/lab09-modules/
├── main.tf                      <- root: calls the module
├── variables.tf                 <- root: inputs
├── outputs.tf                   <- root: re-exports the child's outputs
├── terraform.tfvars.example
└── modules/
    └── network/
        ├── main.tf              <- child: the VPC and subnet resources
        ├── variables.tf         <- child: its inputs (its API)
        └── outputs.tf           <- child: its outputs (its return values)
```

The child module contains the resources; the root contains none. That is a common and healthy
shape — the root becomes a thin assembly of components.

## Calling a module

```hcl
provider "aws" {
  region = var.aws_region
}

# The root module calls the child module. Values go in as arguments,
# results come back out through the child module's outputs.
module "network" {
  source = "./modules/network"

  name        = var.name
  vpc_cidr    = var.vpc_cidr
  subnet_cidr = var.subnet_cidr

  tags = {
    Lab = "lab09"
  }
}
```

| Element | Meaning |
|---|---|
| `module` | The block type |
| `"network"` | The **call name**, chosen by you. It becomes part of every address inside — `module.network.*` |
| `source` | Where the module's code is. Required. `./modules/network` is a path relative to *this* file |
| `name`, `vpc_cidr`, `subnet_cidr`, `tags` | Arguments. Each must match a `variable` declared inside the child |

Passing an argument the child does not declare is an error, and omitting one it declares without a
default is also an error. The child's `variables.tf` is a contract, enforced at plan time.

Note that the `provider` block stays in the **root**. Child modules inherit provider configuration
from their caller by default, which is why the child has no `provider "aws"` block and needs no
region. A module that configured its own provider would be much harder to reuse — the caller could
not decide which region to deploy into.

## The child module

`modules/network/main.tf`:

```hcl
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${var.name}-vpc"
  })
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.subnet_cidr

  tags = merge(var.tags, {
    Name = "${var.name}-subnet"
  })
}
```

Two conventions worth adopting. Naming the sole resource of its type `this` is idiomatic in module
code, because `aws_vpc.network_vpc` inside a module already called `network` stutters. And
`merge(var.tags, { Name = ... })` lets the caller add any tags while the module keeps control of
`Name` — `merge` gives the rightmost map precedence, so the module's own keys win.

`modules/network/variables.tf` defines the module's inputs:

```hcl
# These are the module's inputs. The caller must supply name, vpc_cidr and subnet_cidr.
variable "name" {
  type        = string
  description = "Name prefix applied to every resource in this module."
}

variable "vpc_cidr" {
  type        = string
  description = "IP address range for the VPC."
}

variable "subnet_cidr" {
  type        = string
  description = "IP address range for the subnet."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into every resource in this module."
  default     = {}
}
```

Three have no `default`, making them required. `tags` defaults to an empty map, making it optional.
That distinction is the main design decision when writing a module: required means "I cannot guess
this", optional means "I have a sensible answer".

## Getting values back out

A child module's resources are **invisible from outside**. The root cannot write
`module.network.aws_vpc.this.id`. Only declared outputs cross the boundary:

```hcl
# These are the module's outputs. Only these values are visible to the caller.
output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.this.id
}

output "subnet_id" {
  description = "ID of the created subnet."
  value       = aws_subnet.this.id
}
```

The root then reads them as `module.<call name>.<output name>` and, in lab09, re-exports them so
the CLI displays them:

```hcl
# Root outputs re-export the child module's outputs so the CLI can show them.
output "vpc_id" {
  description = "ID of the VPC created by the network module."
  value       = module.network.vpc_id
}
```

This encapsulation is the reason modules are useful rather than merely tidy. The module's author
can restructure its internals — rename a resource, split it in two, add a NAT gateway — and no
caller breaks, as long as the outputs keep their names and meanings. The output list is the public
API; everything else is an implementation detail.

## Module addresses in state

State addresses are prefixed with the module path:

```text
$ terraform state list
module.network.aws_subnet.this
module.network.aws_vpc.this
```

`module.network.aws_vpc.this` reads as: inside the module call named `network`, the `aws_vpc`
named `this`. Nested modules stack the prefixes —
`module.network.module.subnets.aws_subnet.this`.

These addresses are what you pass to state commands and `-replace`:

```bash
terraform state show module.network.aws_vpc.this
terraform apply -replace=module.network.aws_subnet.this
```

Renaming a `module` block changes every address inside it, and Terraform reads that as "destroy
everything at the old addresses, create everything at the new ones". If you must rename, use
`terraform state mv` (or a `moved` block) to relocate the addresses first — otherwise you will
delete and rebuild a working VPC over a cosmetic change.

## Module sources

| Source | Example | Versioned? |
|---|---|---|
| Local path | `source = "./modules/network"` | No — it is the same repository |
| Terraform Registry | `source = "terraform-aws-modules/vpc/aws"` | Yes, with `version = "~> 5.0"` |
| Git | `source = "git::https://example.com/repo.git//modules/vpc?ref=v1.2.0"` | Yes, via `ref` |

This track uses local paths only, which keeps everything you need in one directory.

Registry and Git sources take a `version` or `ref`, and pinning it is not optional in real work.
An unpinned module means someone else's commit changes your infrastructure without you doing
anything. Local paths need no version because the code moves with your repository.

Note that `terraform init` is what fetches module code. Adding a `module` block or changing a
`source` requires re-running `init`, exactly like adding a provider.

## When to extract a module

Modules have real costs — indirection, a version to manage, a boundary to design — so extract one
for a reason:

**Good reasons**

- The same pattern is genuinely repeated in three or more places.
- Ownership differs: the network team maintains the module, application teams consume its outputs
  and cannot reshape the VPC.
- You need to version it, so consumers can adopt a change deliberately.
- The abstraction is a real concept, not just adjacent lines of code.

**Poor reasons**

- The root file feels long. Splitting into `network.tf`, `compute.tf` in the same root module
  achieves that with no indirection at all.
- Two places share a pattern. Wait for the third; two examples rarely reveal the right boundary.
- Wrapping a single resource so callers pass through every one of its arguments. That adds a layer
  and removes nothing.

## Inputs, outputs, and secrets

- Pass sizing, naming, and CIDRs as variables.
- Do not pass credentials into modules. Providers get credentials from the environment, and the
  child inherits the configured provider.
- Export only what consumers need. Every output is a promise you must keep.
- Type and describe every variable — inside a module this is the only documentation there is.

## Command reference

```bash
cd terraform/labs/lab09-modules
terraform init                                    # also fetches module code
terraform plan
terraform apply
terraform state list                              # addresses are module.network.*
terraform state show module.network.aws_vpc.this
terraform output vpc_id
terraform destroy
```

## Where next

- Multiple providers and multi-stack repository layout:
  [`17-project-structure.md`](17-project-structure.md)
- The capstone that assembles a whole network from these parts: [`08-capstone.md`](08-capstone.md)
- Building many similar resources from one block, instead of many modules:
  [`09-collections-functions.md`](09-collections-functions.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 09: Modules](../labmanuals/lab09-modules.md) | Local child module, pass variables in, read outputs back, module addresses in state |
