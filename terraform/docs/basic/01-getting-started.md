# Getting Started with Terraform

Deep dive for lab00 and lab01. Read this after you have finished those labs and want the
reasoning behind what you typed.

## The idea: declaring instead of doing

Terraform is an **infrastructure as code** tool. "Infrastructure" means the servers, networks,
and other cloud objects your software runs on. "As code" means you write those objects down in
text files that live in version control alongside your application.

The important word is **declarative**. You do not write a list of instructions for Terraform to
follow. You write a description of the end state you want, and Terraform works out the
instructions itself. Compare the three ways you could create one server:

| Approach | What you write | What happens on the second run |
|---|---|---|
| Web console | Nothing. You click. | You click again, and hope you remember the same choices. |
| Shell script (`aws ec2 run-instances ...`) | The steps to take | A second server appears. The script cannot tell it already ran. |
| Terraform | The server you want to exist | Nothing. Reality already matches the description. |

That last row is the whole point. A Terraform configuration is safe to run repeatedly because it
describes an end state, not a sequence of actions. Running it when reality already matches
produces no changes. This property is called **idempotency**.

**New to Terraform entirely?** Read [`../../html/terraform-101.html`](../../html/terraform-101.html)
first — it defines every term from zero. **Visual summary of this tier:**
[`../../html/basic.html`](../../html/basic.html).

## The vocabulary

Six words appear constantly. Learn them now and the rest of the track reads easily.

| Term | Meaning |
|---|---|
| **Configuration** | The `.tf` files in one directory. This is what you write. |
| **Root module** | The directory you actually run `terraform` in. One lab folder = one root module. |
| **Provider** | A plugin that knows how to talk to one API. `hashicorp/aws` speaks to AWS; `hashicorp/random` generates random values locally. |
| **Resource** | An object Terraform creates, updates, and destroys for you — an `aws_instance`, a `random_pet`. Terraform owns it. |
| **Data source** | A read-only lookup of something that already exists. Terraform reads it but never changes it. You meet these in lab03. |
| **Output** | A value Terraform prints after `apply`, so you (or another tool) can use it. |
| **State** | Terraform's record of which real cloud objects belong to which lines of your configuration. Stored in `terraform.tfstate`. |

Every lab directory under [`../../labs/`](../../labs/) is its own root module with its own state
file, so an experiment in one lab can never damage another.

## How the pieces connect

```
you write .tf files
        │
        ▼
terraform init ──> downloads provider plugins into .terraform/
        │
        ▼
terraform plan ──> reads state, refreshes from the API, prints a diff
        │
        ▼
terraform apply ─> calls the cloud API, then updates terraform.tfstate
```

Terraform is not a background service. Nothing happens unless you run a command. There is no
agent watching your account and no daemon reconciling drift on a timer — you invoke Terraform
deliberately, read what it proposes, and approve it.

## Anatomy of a configuration (lab01)

Open [`../../labs/lab01-providers-init/main.tf`](../../labs/lab01-providers-init/). It has three
layers, and almost every Terraform configuration you ever see will have the same three.

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

resource "random_pet" "lab_id" {
  length = 2
}

output "lab_id" {
  value = random_pet.lab_id.id
}
```

1. **`terraform { ... }`** — settings for Terraform itself. Which version of the CLI is
   acceptable, and which provider plugins `init` must download. Notice this block contains no
   infrastructure at all.
2. **`provider "aws" { ... }`** — how to configure a plugin once it is downloaded. Here that is
   only the region. There are no credentials in this block, and there never should be.
3. **`resource` and `output`** — the actual infrastructure, and the values to report afterwards.

Lab01 creates a `random_pet` rather than an EC2 instance on purpose. `random_pet` produces a
name like `helpful-panda` using no cloud API and no money, so you can practise `init`,
`validate`, and `plan` before anything can appear on a bill. The AWS provider is declared but
unused; lab03 is where it starts creating things.

### Reading the block syntax

HCL — HashiCorp Configuration Language, the language `.tf` files are written in — has one
repeating shape:

```
resource      "random_pet"   "lab_id"   {  length = 2  }
└─ block type └─ first label  └─ second   └─ body: argument = value
                 (what kind)     label
                                 (your name for it)
```

For `resource` blocks the first label is the resource **type** (fixed, defined by the provider)
and the second is the **name** you choose (any valid identifier, unique within the type). You
then refer to the thing you created by joining them with the attribute you want:

- `random_pet.lab_id.id` — the `id` attribute of the `random_pet` named `lab_id`
- `var.aws_region` — the value of an input variable (lab06)
- `local.common_tags` — a value computed inside the configuration (lab06)

Values come in the usual types: strings in double quotes, numbers bare, booleans `true`/`false`,
lists in `[]`, maps in `{}`. Comments use `#`.

## Version constraints

Two different things get versioned, and they are easy to confuse.

- **`required_version`** constrains the Terraform CLI itself.
- **`version` inside `required_providers`** constrains a provider plugin.

| Constraint | Allows | Excludes |
|---|---|---|
| `>= 1.5.0` | 1.5.0, 1.9.4, 2.0.0 — anything newer | 1.4.7 and older |
| `~> 5.0` | 5.0.0 through 5.99.x — the newest 5.x | 4.x, and 6.0.0 |
| `~> 3.0` | any 3.x release of the random provider | 2.x, 4.0.0 |

The `~>` operator is called **pessimistic**. `~> 5.0` means "allow the last number to move
freely, pin everything to its left", which for a two-part constraint permits any 5.x but blocks
the 6.0 major release where argument names may change. This whole track uses
`required_version = ">= 1.5.0"` and AWS provider `~> 5.0`.

After `terraform init`, Terraform writes `.terraform.lock.hcl`. The constraint says which
versions are *acceptable*; the lock file records which one you *actually got*, with checksums.
Commit the lock file so your teammates and your CI system resolve the same provider build you
did. Add `.terraform/` — the downloaded plugin binaries, tens of megabytes — to `.gitignore`.

## Authentication (lab00)

Credentials never go in `.tf` files. Not in a variable default, not in a comment, and above all
not in git — a leaked AWS key is somebody else's compute bill and your incident report. The
`provider "aws"` block gets the region and nothing else.

The AWS provider looks for credentials the same way the `aws` CLI does, checking several places
in order. Lab00 uses the first and simplest: environment variables.

```bash
unset AWS_PROFILE AWS_SESSION_TOKEN
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

An **access key ID** (starts with `AKIA`) names the identity; the **secret access key** proves
it. The ID is merely identifying, the secret is a password — treat it like one.

Unsetting `AWS_PROFILE` first matters. If it is still set from earlier work it takes precedence
and you will authenticate as the wrong identity, or fail outright. Do not try to neutralise it by
setting it to an empty string — that produces the confusing error
`The config profile () could not be found`. Actually unset the variable.

The alternate route is a named profile stored on disk:

```bash
aws configure --profile tf-labs
```

```hcl
provider "aws" {
  region  = "us-east-1"
  profile = "tf-labs"
}
```

Either way, confirm who you are before running Terraform:

```bash
aws sts get-caller-identity
```

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/tf-labs"
}
```

If that returns an ARN, your credentials work. One thing it does not tell you is what you are
*allowed* to do: lab and sandbox accounts are usually permission-scoped, so an
`UnauthorizedOperation` error later on is a policy boundary, not a broken credential. Rotate or
delete the keys when you finish the track.

## Common mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| `terraform validate` before `init` | Validation needs the provider schemas, which `init` downloads | Run `terraform init` first |
| `access_key` in the `provider` block | Ends up in git forever | Environment variables or a named profile |
| Running from the `labs/` parent | Terraform only reads `.tf` files in the current directory | `cd` into exactly one lab folder |
| Forgetting `destroy` on AWS labs | Resources bill by the hour | `terraform destroy` when the lab is done |
| Committing `.terraform/` | Large binaries, machine-specific | Commit `.terraform.lock.hcl` only |
| `AWS_PROFILE=""` to disable a profile | Empty string is still a value | `unset AWS_PROFILE` |

## Command reference

```bash
cd terraform/labs/lab01-providers-init
terraform version      # confirm >= 1.5.0
terraform init         # download providers, write the lock file
terraform validate     # syntax and reference check, no API calls
terraform plan         # show what would change
terraform apply        # make it so
terraform destroy      # tear it back down
```

## Where next

- Providers and the lock file in depth: [`02-providers.md`](02-providers.md)
- Never opened the AWS console? [`../../html/aws-primer.html`](../../html/aws-primer.html)
  defines regions, VPCs, subnets, and security groups.

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 00: AWS Setup and Init](../../labmanuals/lab00-aws-setup-and-init.md) | Credentials, the provider block, first `terraform init` |
| [Lab 01: Providers and Init](../../labmanuals/lab01-providers-init.md) | `required_providers`, the lock file, `validate`, `plan` |
