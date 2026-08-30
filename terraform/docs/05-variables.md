# Terraform Variables, Locals, and Outputs

Backs labs 06 and 07. Covers the three kinds of named value, the full precedence order when the same
variable is set twice, type constraints and validation, and how `sensitive` behaves on an input.

## Three kinds of named value

Everything hardcoded in labs 00–05 becomes a parameter here. Terraform has three constructs for
naming a value, and choosing correctly is mostly about **who is allowed to set it**.

| Construct | Set by | Visible to | Use for |
|---|---|---|---|
| `variable` | The caller — CLI flag, tfvars file, environment variable, or a `module` block | Inside this module | Anything that legitimately differs between environments: region, size, name, CIDR |
| `local` | The configuration itself. Nobody outside can override it | Inside this module | Values derived from other values: merged tags, composed names, repeated expressions |
| `output` | The configuration | The caller, and other configurations | Results worth reporting: IDs, ARNs, URLs |

Variables point **in**, outputs point **out**, locals stay **inside**. A local is not a variable
with a default — the difference is that a default can be overridden and a local cannot. If you do
not want a caller changing something, make it a local.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Declaring a variable

Every variable in this track declares a `type` and a `description`. Both are technically optional
and both should be treated as mandatory.

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region the instance is created in."
  default     = "us-east-2"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size."
  default     = "t3.micro"
}

variable "server_name" {
  type        = string
  description = "Value used for the Name tag on the EC2 instance."
  default     = "lab06-web"
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
```

- **`type`** turns a whole class of mistake into an immediate, clear error. Without it Terraform
  infers the type from whatever arrives, and a list supplied where a string was meant fails later
  and more confusingly.
- **`description`** is the only documentation a module consumer gets. It appears in error messages
  and in generated docs.
- **`default`** makes the variable optional. **Omit `default` to make it required** — Terraform
  then refuses to plan until a value is supplied. That is the right choice for anything with no
  safe default, which is why lab07 gives `db_password` no default at all.

### The type system

| Type | Example value | Notes |
|---|---|---|
| `string` | `"us-east-2"` | Double quotes |
| `number` | `80` | Integers and decimals |
| `bool` | `true` | Not `"true"` |
| `list(string)` | `["a", "b"]` | Ordered, duplicates allowed, indexed by position |
| `set(string)` | `["a", "b"]` | Unordered, duplicates silently dropped |
| `map(string)` | `{ Env = "dev" }` | Keyed by string. All values the same type |
| `object({...})` | `{ cidr = string, az = string }` | Fixed named fields, each with its own type |
| `any` | anything | Disables checking. Avoid |

Lab11 explores the difference between list, set, and map properly —
[`09-collections-functions.md`](09-collections-functions.md).

## Locals

A `local` computes a value once and reuses it. Lab06 uses one to build a tag map:

```hcl
locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
    Lab  = "lab06"
  })
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.instance.id]
  tags                   = local.common_tags
}
```

`merge` combines maps left to right; on a duplicate key the **rightmost wins**. So the caller can
supply anything in `var.tags`, but `Name` and `Lab` are set by the configuration and cannot be
overridden — exactly the behaviour you want for a tag your cleanup process depends on.

The payoff is single-point change. Every resource using `local.common_tags` picks up a new tag the
moment it is added in one place. Note also that locals reference `var.*` freely, and other locals
too, as long as there is no cycle.

The network in that snippet is lab06's own. `vpc_cidr`, `subnet_cidr` and `subnet_az` are variables,
and the VPC, subnet and security group they describe are resources the lab creates, so the instance
names the subnet it launches into rather than inheriting the account's default VPC. Port 22 is open
only to `var.vpc_cidr`, and there is no internet gateway, so nothing outside that VPC can connect —
the same design as lab03, for the same reason
([`02-resources.md`](02-resources.md)).

## Where a value can come from

Terraform accepts variable values from six places. When the same variable is set more than once,
**the last one to be evaluated wins** — highest precedence first:

| Precedence | Source | Notes |
|---|---|---|
| 1 (highest) | `-var 'name=value'` on the command line | Beats everything |
| 2 | `-var-file=FILE` | In the order the flags appear |
| 3 | `*.auto.tfvars` / `*.auto.tfvars.json` | Loaded automatically, alphabetically by filename |
| 4 | `terraform.tfvars.json` | |
| 5 | `terraform.tfvars` | Loaded automatically if present. The usual place for local values |
| 6 | `TF_VAR_name` environment variable | e.g. `export TF_VAR_db_password=...` |
| 7 (lowest) | `default` in the `variable` block | The fallback |
| — | Interactive prompt | Only if no value exists anywhere and there is no default |

Two practical consequences. A `default` is the weakest possible source, so it is safe to think of
it as documentation of the sensible value rather than a real setting. And `TF_VAR_` sits above
defaults but below every file, which makes it the natural home for secrets: the value never
touches disk, so it cannot be committed.

## tfvars files

A `.tfvars` file is just variable assignments:

```hcl
project     = "tflabs"
environment = "dev"
cost_code   = "abc"
```

The convention this track uses — and one worth copying — is to commit
`terraform.tfvars.example` and gitignore the real `terraform.tfvars`. The example documents every
variable a user must set, with placeholder values, while the real file holds their actual values
and never enters version control. A new contributor copies one to the other and fills it in.

Never put a secret in a committed tfvars file. Use `TF_VAR_` or a secrets manager.

## Validation (lab07)

A `validation` block rejects bad input at plan time, with your error message rather than a
provider's:

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment, lowercase. Set in terraform.tfvars."

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "cost_code" {
  type        = string
  description = "Three-character billing code. Set in terraform.tfvars."

  validation {
    condition     = length(var.cost_code) == 3
    error_message = "cost_code must contain exactly three characters."
  }
}
```

`condition` must evaluate to `true` for the value to be accepted, and it may only reference the
variable being validated. This is a much better failure than the alternative: without it, a
misspelled `Prod` propagates into resource names and tags and you find out from an AWS error, or
from a mis-tagged bill, long after the fact.

## Sensitive variables and outputs (lab07)

Mark an input sensitive when it carries a secret:

```hcl
variable "db_password" {
  type        = string
  description = "Database password. Never put this in a committed file; export TF_VAR_db_password instead."
  sensitive   = true
}
```

Terraform then redacts the value in plan and apply output, and — importantly — **propagates the
mark**. Any value computed from a sensitive value is itself sensitive, so a secret cannot leak by
being embedded in a resource name or a tag that Terraform then prints.

Lab07 shows all three behaviours side by side:

```hcl
output "settings" {
  description = "Non-secret values, safe to print."
  value       = local.settings
}

output "db_password" {
  description = "Marked sensitive, so the CLI prints (sensitive value) instead of the password."
  value       = var.db_password
  sensitive   = true
}

output "db_password_length" {
  description = "Proof the password arrived, without revealing it. nonsensitive() unmarks the value."
  value       = nonsensitive(length(var.db_password))
}
```

The third output is the interesting one. `length(var.db_password)` inherits the sensitive mark
from its input, so Terraform would refuse to display it even though a password's length is not a
secret. `nonsensitive()` deliberately removes the mark. It is an assertion that you have thought
about it — use it only on values that genuinely reveal nothing, and never on the secret itself.

### How far redaction actually goes

This is the point most often misunderstood, so be precise about it:

| Command | Shows the value? |
|---|---|
| `terraform plan` / `terraform apply` summary | No — `(sensitive value)` |
| `terraform output` with no arguments | No — `<sensitive>` |
| `terraform output db_password` | **Yes, in full** |
| `terraform output -raw db_password` | **Yes, in full**, without quotes |
| `terraform output -json` | **Yes, in full** |
| `terraform.tfstate` on disk | **Yes, in plain text** |

You do **not** need `-raw` to reveal a sensitive value; naming the output is enough. `-raw` only
strips the quotes so the value can be piped elsewhere.

So `sensitive = true` prevents accidental disclosure — a secret scrolling past in a screen share
or landing in a CI log. It is not access control. Anyone who can run Terraform in that directory
can read the value, and anyone with the state file already has it. The actual protection is
guarding state, covered in [`06-state.md`](06-state.md).

## Command reference

```bash
cd terraform/labs/lab06-variables-outputs
terraform init
terraform plan                                   # uses every default
terraform plan -var="server_name=demo-web"       # override one variable
terraform apply -var-file=terraform.tfvars       # override from a file
terraform output applied_tags                    # inspect the merged tag map
terraform destroy

cd ../lab07-tfvars-secrets
cp terraform.tfvars.example terraform.tfvars
export TF_VAR_db_password="not-in-a-file"
terraform apply
terraform output                     # db_password shows as <sensitive>
terraform output db_password         # named: prints in full
terraform output db_password_length  # nonsensitive() length, no secret revealed
```

## Where next

- Where variable values end up recorded, and why that is a secrets problem:
  [`06-state.md`](06-state.md)
- Passing variables into a reusable child module: [`07-modules.md`](07-modules.md)
- List, set, and map in depth: [`09-collections-functions.md`](09-collections-functions.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 06: Variables and Outputs](../labmanuals/lab06-variables-outputs.md) | Typed variables, locals, merged tags on an EC2 instance, outputs |
| [Lab 07: tfvars and Secrets](../labmanuals/lab07-tfvars-secrets.md) | tfvars files, `validation` blocks, sensitive variables, `nonsensitive()` |
