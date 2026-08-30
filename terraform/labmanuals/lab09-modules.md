# Lab 09 — Modules

| | |
|---|---|
| **Goal** | Call a reusable child module that builds a VPC and a subnet, passing values in as module arguments and reading results back out through module outputs. |
| **Time** | 50–60 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab09-modules/` |

## Overview

A **module** is a directory of `.tf` files. That is the whole definition. Every configuration you
have written so far was already a module — the **root module**, the directory you run `terraform`
in. What is new here is calling *another* module from it. A module you call is a **child module**,
and calling it is how you stop copying the same twenty lines of HCL into every project.

Think of a child module as a function. It has inputs (its `variable` blocks), a body (its
`resource` blocks), and return values (its `output` blocks). The caller sets the inputs, cannot
reach inside the body, and can only read what the outputs expose. Those boundaries are the point:
the module author can rewrite the internals and callers do not care, as long as the inputs and
outputs stay the same.

This lab calls a `network` module that creates a VPC and one subnet. A **VPC** is your own private
network inside an AWS region; a **subnet** is a slice of that network's IP range. Both are free.
Most of this lab is spent reading the four places the module boundary shows up — the child's
inputs, the child's outputs, the call site, and the `module.` prefix in plan and state — because
once you can see the boundary, every other module you meet works the same way.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `modules/network/` | The reusable child module | — |
| `aws_vpc.this` | Private network `10.42.0.0/16`, created inside the module | Free |
| `aws_subnet.this` | Subnet `10.42.1.0/24` inside that VPC | Free |
| Root outputs | `vpc_id`, `subnet_id`, re-exported from the module | — |

## Before you start

- [ ] Lab 08 completed ([lab08-local-state.md](lab08-local-state.md))
- [ ] You can declare a variable with a `type` and read an output (Lab 06)
- [ ] AWS credentials exported and `aws sts get-caller-identity` succeeds
- [ ] Working directory: `../labs/lab09-modules/`

## Steps

### Step 1 — Look at the two-level layout

```bash
cd terraform/labs/lab09-modules
find . -name '*.tf' | sort
```

**Expected output**

```text
./main.tf
./modules/network/main.tf
./modules/network/outputs.tf
./modules/network/variables.tf
./outputs.tf
./variables.tf
```

Six files at two levels. The top level is the root module — the directory you run commands in.
`modules/network/` holds the child module: a self-contained set of files with its own variables
and outputs.

### Step 2 — Read the child module's inputs

```bash
cat modules/network/variables.tf
```

**Expected output**

```text
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

This file is the module's contract. These four names are the only way information gets in. Three
of them have no `default`, so any caller **must** supply `name`, `vpc_cidr`, and `subnet_cidr`;
`tags` defaults to an empty map and is optional.

### Step 3 — Read the child module's body

```bash
cat modules/network/main.tf
```

**Expected output**

```text
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

Every value these two resources need comes from `var.*` — no hardcoded CIDRs and no hardcoded
names, which is what makes the module reusable. Note also what is *absent*: there is no `provider`
block and no `terraform` block. A child module inherits the provider configured by the root module,
so it must not declare its own.

### Step 4 — Read the child module's outputs

```bash
cat modules/network/outputs.tf
```

**Expected output**

```text
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

These two values are the entire return surface of the module. The caller cannot write
`aws_vpc.this.id`, because resources inside a module are invisible from outside. If a caller needs
something the module does not output, the module has to be changed to output it.

### Step 5 — Read the `module` call block in the root

```bash
grep -A 12 'module "network"' main.tf
```

**Expected output**

```text
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

`source` says where the module's files are — here a relative path. `network` is the local name for
this call, and it is what you will see in every address later on. The remaining arguments set the
child module's input variables, one for one against the file you read in Step 2. The root module
passes its own variables straight through, so a value overridden on the command line still reaches
the module.

### Step 6 — Read the root outputs that re-export the module's

```bash
cat outputs.tf
```

**Expected output**

```text
# Root outputs re-export the child module's outputs so the CLI can show them.
output "vpc_id" {
  description = "ID of the VPC created by the network module."
  value       = module.network.vpc_id
}

output "subnet_id" {
  description = "ID of the subnet created by the network module."
  value       = module.network.subnet_id
}
```

A child module's outputs are not printed automatically. To get `vpc_id` onto your screen you have
to reference it as `module.network.vpc_id` from the root. `module.<call name>.<output name>` is the
general form, and it is also how you feed one module's result into another module's input.

### Step 7 — Initialize, and watch the module load separately from the provider

```bash
terraform init
```

**Expected output**

```text
Initializing the backend...
Initializing modules...
- network in modules/network
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)
...
Terraform has been successfully initialized!
```

`Initializing modules...` is new in this lab, and it is a separate phase from
`Initializing provider plugins...`. Module loading resolves every `source` and records where those
files live; provider installation downloads plugins. They fail for different reasons, so read them
as two things. `init` must be re-run whenever you add or change a `module` block. Your provider
version may be newer than `v5.100.0`.

### Step 8 — Inspect the module boundary in the console

```bash
echo 'module.network' | terraform console
```

**Expected output**

```text
{
  "subnet_id" = (known after apply)
  "vpc_id" = (known after apply)
}
```

This is the clearest view of the boundary you will get. From the root module, the entire `network`
module is a single object with exactly two attributes — the two outputs from Step 4. The VPC and
subnet resources are not in this object, because they are not part of what the module returns.
`(known after apply)` simply means nothing has been created yet.

### Step 9 — Plan and read the module addresses

```bash
terraform plan
```

**Expected output**

```text
  # module.network.aws_subnet.this will be created
  # module.network.aws_vpc.this will be created

Plan: 2 to add, 0 to change, 0 to destroy.
```

The resource addresses are prefixed with `module.network.`. Inside the child module the resource is
just `aws_vpc.this`; from outside it is `module.network.aws_vpc.this`. That prefix is how Terraform
keeps two calls to the same module from colliding.

### Step 10 — Apply

```bash
terraform apply
```

Type `yes` at the prompt.

**Expected output**

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

subnet_id = "subnet-0abc123def4567890"
vpc_id = "vpc-0abc123def4567890"
```

Your IDs will differ. Both values reached the screen by travelling the whole path: resource
attribute, then child module output, then root output.

### Step 11 — Resolve a `module.<name>.<output>` reference

```bash
echo 'module.network.vpc_id' | terraform console
terraform output -raw vpc_id
```

**Expected output**

```text
"vpc-0abc123def4567890"
vpc-0abc123def4567890
```

The same value, reached two ways. The console line evaluates the module reference directly, which
is what your `outputs.tf` does internally. `terraform output -raw` reads the root output that wraps
it, with no quotes, which is the form you pipe into other commands.

### Step 12 — Confirm the module prefix reached state

```bash
terraform state list
```

**Expected output**

```text
module.network.aws_subnet.this
module.network.aws_vpc.this
```

State records the prefixed addresses, not the bare ones. This is why moving a resource into or out
of a module is a state operation and not just an edit — the address changes.

### Step 13 — Confirm the tags the module merged

```bash
aws ec2 describe-tags \
  --filters "Name=resource-id,Values=$(terraform output -raw vpc_id)" \
  --query 'Tags[].[Key,Value]' --output text
```

**Expected output**

```text
Lab	lab09
Name	lab09-vpc
```

`Name` was built inside the module as `"${var.name}-vpc"`. `Lab` came from the `tags` argument at
the call site in Step 5. The module's `merge()` combined the two, which is how a module accepts
caller-supplied tags without losing its own.

### Step 14 — Destroy

```bash
terraform destroy
```

Type `yes` at the prompt.

**Expected output**

```text
Destroy complete! Resources: 2 destroyed.
```

Terraform destroys resources inside a module exactly as it would at the root; the `module.network.`
prefix appears in the destroy plan too.

## Done when

- [ ] You can name the child module's four inputs and two outputs without opening the files
- [ ] `terraform init` reports `network in modules/network` as a phase separate from provider install
- [ ] `terraform console` shows `module.network` as an object with exactly two attributes
- [ ] Plan and state addresses are prefixed with `module.network.`
- [ ] `apply` prints `vpc_id` and `subnet_id` via the root outputs
- [ ] The VPC carries both `Name = lab09-vpc` and `Lab = lab09`
- [ ] `terraform destroy` reports `2 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Module not installed` | A `module` block was added or edited after `init` | Run `terraform init` again |
| `Unsupported argument` in the `module` block | Argument is not one of the module's variables | Match `modules/network/variables.tf` exactly |
| `Missing required argument` | A module variable with no `default` was not set | Supply `name`, `vpc_cidr`, and `subnet_cidr` |
| `module.network has no attribute X` | Referenced a value the module does not output | Add an `output` to the child module |
| `Reference to undeclared resource` | Tried to use `aws_vpc.this` from the root module | Go through `module.network.vpc_id` |
| `InvalidSubnet.Range` | `subnet_cidr` is not inside `vpc_cidr` | Keep the subnet within `10.42.0.0/16` |
| `VpcLimitExceeded` | Account is at its VPC quota | Destroy an unused VPC in this region |

## Cleanup

```bash
terraform destroy
```

## Next steps

- Deep dive: [docs/07-modules.md](../docs/07-modules.md)
- Visual: [html/intermediate.html](../html/intermediate.html)
- Continue to [Lab 10 — Capstone: VPC and EC2](lab10-capstone-vpc-ec2.md)
