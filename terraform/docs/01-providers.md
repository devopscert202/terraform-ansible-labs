# Terraform Providers

Backs labs 01 and 02. Covers what a provider actually is, how `init` resolves one, what the lock
file protects you from, the difference between a resource and a data source, and — since lab02 builds
a network by hand in the AWS console — what a provider is saving you from doing yourself.

## What a provider is

Terraform core knows nothing about AWS. It does not know that an EC2 instance exists, what
arguments one takes, or which API endpoint creates it. All of that lives in a **provider** — a
separately versioned plugin that Terraform downloads and runs as a child process.

The division of labour is worth understanding, because it explains most of Terraform's error
messages:

| Layer | Responsibility |
|---|---|
| Terraform core | Parsing HCL, building the dependency graph, computing the diff, managing state |
| Provider plugin | Knowing that `aws_instance` exists, which arguments it accepts, and which API calls create it |
| Cloud API | Actually doing the work |

So "Invalid resource type" is core failing to find a type in the provider's schema, while
"UnauthorizedOperation" came all the way back from AWS. Two very different problems.

Providers are published to the **Terraform Registry** at `registry.terraform.io`. An address like
`hashicorp/aws` is shorthand for `registry.terraform.io/hashicorp/aws` — namespace `hashicorp`,
provider name `aws`. The namespace tells you who maintains it, which matters: `hashicorp/aws` is
official, but anyone can publish under their own namespace.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Declaring a provider

Two separate blocks are involved, and beginners routinely conflate them.

| Block | Answers | Read by |
|---|---|---|
| `required_providers` (inside `terraform {}`) | *Which* plugin, and which versions are acceptable | `terraform init`, at download time |
| `provider "aws" {}` | *How* to configure that plugin — region, profile, endpoints | `plan` and `apply`, at run time |

They are separate because they happen at different times. `init` needs to know what to download
before it can read anything else; configuration is only meaningful once the plugin is present.

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
  region = "us-east-2"
}
```

- `aws = { ... }` — the key is the **local name**. It is what resource type prefixes match
  against, which is why `aws_instance` resources use this provider.
- `source` — the registry address, telling `init` where to fetch from.
- `version` — the acceptable range. `~> 5.0` accepts any 5.x and refuses 6.0.

The `random` provider needs no `provider` block at all here, because it has nothing to configure
and no credentials. Declaring it in `required_providers` is enough.

## Why lab01 declares two providers

Lab01 registers both AWS and Random but creates only a `random_pet`. That is deliberate. You get
to watch `init` resolve and download two plugins, and inspect a lock file with two entries,
without any possibility of an AWS charge. The AWS declaration also establishes the pattern that
every later AWS lab reuses unchanged.

## What `init` actually does

```
terraform init
  │
  ├─ read required_providers
  ├─ query registry.terraform.io for versions matching each constraint
  ├─ pick the newest match for each
  ├─ download the plugin binary  ->  .terraform/providers/...
  ├─ verify its checksum
  └─ write/update .terraform.lock.hcl
```

`.terraform/` holds the binaries. It is machine-specific and large, so it belongs in
`.gitignore`. `.terraform.lock.hcl` is small, portable, and **should be committed**.

## The lock file

The version constraint and the lock file do different jobs, and confusing them causes the classic
"it worked on my machine" failure.

- The **constraint** (`~> 5.0`) says which versions are permitted. It is a range.
- The **lock file** records the exact version you resolved to, plus checksums of the binary. It
  is a single point.

Without a committed lock file, you and your colleague both satisfy `~> 5.0` and end up on
different 5.x releases. If a minor release changed a default, your plans differ for no visible
reason. With the lock file committed, `init` installs precisely what the file names.

To move deliberately to a newer version, widen or change the constraint and then:

```bash
terraform init -upgrade
```

`-upgrade` is the only thing that re-resolves within the constraint and rewrites the lock file.
Plain `init` respects the lock. After upgrading, always read the plan carefully — a provider
release can change a computed default and produce a diff you did not write.

## Resources versus data sources

This is the other half of the provider story, and the distinction is about **ownership**.

| | `resource` | `data` |
|---|---|---|
| Terraform creates it? | Yes | No, it already exists |
| Terraform destroys it? | Yes, on `destroy` | No, never |
| Appears in state as managed? | Yes | Read cached, not managed |
| Reference prefix | `aws_instance.web` | `data.aws_ami.amazon_linux` |
| When evaluated | Create/update/destroy during apply | Read during plan and apply |

A data source answers a question. A resource makes a promise. Asking Terraform to `resource` a
thing it did not create is a common beginner error and produces a name-conflict failure from the
API.

## Doing it by hand instead (lab02)

Lab02 is the only lab in the track with no Terraform code. You build a VPC, subnet, internet gateway,
route table and security group by clicking through the AWS console, then delete them by hand. It is
there to give you something to compare against, and three things are worth noticing while you click.

- **Order is your problem.** The console will happily let you create a subnet before there is
  anywhere sensible to put it, and a route table that points at a gateway you have not attached. You
  have to know the sequence. Terraform derives it from your references instead — see
  [`02-resources.md`](02-resources.md).
- **Nothing is written down.** When you finish, the only record of what you built is the account
  itself. There is no file to review, no diff, no history of who changed the CIDR range.
- **Deleting is worse than creating.** Teardown must happen in reverse dependency order, and AWS
  refuses each step until its dependents are gone. `terraform destroy` is one command because
  Terraform already knows that order.

Lab10 builds this same network from one file. Keep lab02 in mind when you get there.

## The AMI data source (lab03)

The clearest use of a data source is finding a machine image. An **AMI** (Amazon Machine Image)
is the disk image an EC2 instance boots from. Every AMI has an ID like `ami-0abc123...`, and
those IDs are the wrong thing to put in your configuration for two reasons: they differ in every
region, and AWS publishes a replacement image every few weeks, so a hardcoded ID slowly rots
until it is deleted and your `apply` fails.

So lab03 asks AWS for the newest Amazon Linux 2023 image at plan time instead:

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.instance.id]

  tags = {
    Name      = var.instance_name
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
}
```

| Line | What it does |
|---|---|
| `most_recent = true` | Several images match the filters; take the newest by creation date |
| `owners = ["amazon"]` | Only images published by Amazon itself. Without this you could match a stranger's public image with a lookalike name — this argument is a security control, not a filter for tidiness |
| `filter { name = "name" ... }` | Match on the image's name field. `al2023-ami-2023.*-x86_64` is the Amazon Linux 2023 naming pattern; the `*` absorbs the date stamp |
| `filter { name = "virtualization-type" ... }` | `hvm` is the modern virtualization type — excludes ancient images |
| `ami = data.aws_ami.amazon_linux.id` | The instance consumes the looked-up ID. Note the `data.` prefix, required for every data source reference |

Because `most_recent = true` reads live data, the resolved ID can legitimately change between
runs when AWS publishes a new image. Changing an `aws_instance`'s `ami` forces the instance to be
replaced, so `plan` may propose a replacement you did not ask for. That is correct behaviour, and
it is the trade for never having a dead hardcoded ID. Production configurations that need
stability pin the AMI through a variable fed by a separate, deliberate update process.

## Provider aliases

One `provider` block per provider is the default. When you need the same provider configured two
different ways — most often two regions — you add an `alias`:

```hcl
provider "aws" {
  region = "us-east-2"
}

provider "aws" {
  alias  = "east1"
  region = "us-east-1"
}

resource "aws_vpc" "east1_vpc" {
  provider   = aws.east1
  cidr_block = "10.1.0.0/16"
}
```

Resources without a `provider` argument use the unaliased default. This track uses a single
`us-east-2` provider everywhere until lab13, which is where multiple providers in one
configuration get proper treatment.

## Command reference

```bash
cd terraform/labs/lab01-providers-init
terraform init          # download providers, write the lock file
terraform providers     # tree of which providers the config and state require
terraform version       # CLI version plus resolved provider versions
terraform init -upgrade # re-resolve within the constraint, rewrite the lock file
```

## Where next

- What resources and data sources do once you have a provider: [`02-resources.md`](02-resources.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 01: Providers and Init](../labmanuals/lab01-providers-init.md) | Declare providers, run `init`, inspect the lock file |
| [Lab 02: Building a network by hand in the console](../labmanuals/lab02-console-vpc.md) | Click through a VPC, subnet, gateway, route table and security group — and delete them by hand |
