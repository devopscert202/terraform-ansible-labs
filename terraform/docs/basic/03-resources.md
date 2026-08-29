# Terraform Resources and Data Sources

Deep dive for lab02 and lab03. Covers what it means for Terraform to *own* a resource, how
resources are addressed and referenced, how Terraform works out the order to build things in, and
why tags matter more than they look.

## Ownership is the whole idea

A **resource** is an object Terraform owns. Ownership means three specific things: Terraform knows
the object's real ID, it records the object's attributes in state, and it will create, modify, or
delete the object to make reality match your configuration.

A **data source** is a read-only question. Terraform reads it and never changes it.

The shortest way to keep them straight: a resource is a **promise** Terraform makes about the
world, while a data source is a **question** it asks about the world. Anything inside a `resource`
block is something you are claiming responsibility for — including its eventual deletion.

**Visual summary:** [`../../html/basic.html`](../../html/basic.html)

## The cost of not having this (lab02)

Lab02 is the only lab in the track with no Terraform code. You build a VPC, subnet, internet
gateway, route table, and security group by clicking through the AWS console, then delete them by
hand.

It is there to give you something to compare against. Three things are worth noticing while you
click:

- **Order is your problem.** The console will happily let you create a subnet before there is
  anywhere sensible to put it, and a route table that points at a gateway you have not attached.
  You have to know the sequence. Terraform derives the sequence itself, as described below.
- **Nothing is written down.** When you finish, the only record of what you built is the account
  itself. There is no file to review, no diff, no history of who changed the CIDR range.
- **Deleting is worse than creating.** Teardown must happen in reverse dependency order, and AWS
  refuses each step until its dependents are gone. `terraform destroy` is one command because
  Terraform already knows that order.

Lab21 builds the same network from one file. Keep lab02 in mind when you get there.

## Resource syntax and addressing

```hcl
resource "aws_instance" "web" {
  instance_type = "t3.micro"
}
```

- `resource` — the block type.
- `"aws_instance"` — the resource **type**. Fixed by the provider. The prefix before the first
  underscore (`aws`) is how Terraform decides which provider handles it.
- `"web"` — the **name**, chosen by you. It must be unique among resources of the same type in
  the same module, and it exists only inside Terraform. AWS never sees it.

Joined with a dot, type and name form the resource's **address**: `aws_instance.web`. Addresses
are how you reference the resource elsewhere in your configuration, and the same addresses appear
in `terraform state list` and in plan output. Add a third segment to read an attribute:

| Reference | Reads |
|---|---|
| `aws_instance.web.id` | The instance ID AWS assigned, e.g. `i-0a1b2c3d` |
| `aws_instance.web.arn` | Its full Amazon Resource Name |
| `aws_instance.web.public_ip` | Its public address, once it has one |
| `data.aws_ami.amazon_linux.id` | An attribute of a *data source* — note the mandatory `data.` prefix |

### Arguments you set versus attributes you read

Some fields you write; others the provider fills in. `instance_type` is an **argument** — you
supply it. `id`, `arn`, and `public_ip` are **computed attributes** — they do not exist until AWS
creates the object, which is why `plan` displays them as `(known after apply)`. You can read them
in outputs and in other resources, but you cannot set them.

## Dependencies are inferred, not declared

This is the part that makes Terraform more than a fancy script. You never tell Terraform what
order to build things in. It reads your references and builds a dependency graph.

In lab03, the instance's `ami` argument references the AMI data source:

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
}
```

Because `aws_instance.web` mentions `data.aws_ami.amazon_linux`, Terraform knows the lookup must
resolve first. That is an **implicit dependency**, and it is the kind you should always prefer —
it cannot go stale, because it is derived from the code itself. Terraform also parallelises
everything the graph shows to be independent, and reverses the graph on `destroy`.

Occasionally a real dependency exists that no reference expresses — resource B needs A to exist,
but reads nothing from it. Then you state it explicitly:

```hcl
resource "aws_instance" "web" {
  # ...
  depends_on = [aws_route_table_association.public]
}
```

Lab21 uses exactly this, because an instance's user-data script needs working internet routing to
install packages, yet the instance reads no attribute from the route table association. Use
`depends_on` sparingly; if you find yourself adding many, you are usually missing a reference.

## Lab03: your first real AWS resource

Lab03 creates one EC2 instance and nothing else. Its whole configuration is a `terraform` block, a
provider, one data source, and one resource:

```hcl
provider "aws" {
  region = var.aws_region
}

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
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = {
    Name      = var.instance_name
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
}
```

Three details deserve attention.

**The AMI is looked up, never hardcoded.** An **AMI** (Amazon Machine Image) is the disk image the
instance boots from. Its ID differs in every region and is replaced every few weeks as Amazon
publishes patched images, so a literal `ami-0abc123...` in your configuration is a time bomb: it
works today, and fails in three months when the image is deregistered. The data source asks for
"newest Amazon Linux 2023" and gets a currently valid ID every time. `owners = ["amazon"]` is not
decoration — without it, a public image from an unrelated account with a similar name could match.

**The instance type is `t3.micro`.** That is the size — 2 vCPU, 1 GiB memory. It is the smallest
current-generation general-purpose size, and it is what every AWS lab in this track uses.

**There is no security group and no subnet.** Lab03 deliberately creates the instance in your
account's default VPC with no inbound rules. You can see the instance exists and read its ID, but
you cannot reach it. Networking arrives properly in lab21. This keeps lab03 to a single new
concept.

## Outputs

An `output` publishes a value after `apply`:

```hcl
output "instance_id" {
  description = "The id AWS assigned to the new instance."
  value       = aws_instance.web.id
}

output "ami_id" {
  description = "The Amazon Linux 2023 image the data source resolved to."
  value       = data.aws_ami.amazon_linux.id
}
```

Outputs change nothing about how Terraform manages infrastructure — a configuration with no
outputs works identically. They exist so a human can read the result without digging through
state, and so other tooling can consume it. `ami_id` above is a good habit: it records which image
this apply actually used, which is the first thing you want to know if a later plan proposes
replacing the instance.

## Tags

```hcl
tags = {
  Name      = var.instance_name
  Lab       = "lab03"
  ManagedBy = "Terraform"
}
```

Tags are free-form key/value labels on an AWS resource. `Name` is special only in that the console
displays it as the object's title; the rest are conventions. They pay for themselves in three
places: filtering the console when an account has hundreds of objects, splitting the bill by team
or project in Cost Explorer, and — most relevant here — telling a human whether an object is
Terraform-managed. An untagged instance nobody recognises is one nobody dares delete.

Every AWS resource in this track carries `Name` and `Lab = "labNN"`, so you can always find and
clean up everything a given lab created. Interpolating a variable (`var.instance_name`) rather
than a literal means one variable renames every related object at once.

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Hardcoded `ami-0abc123...` | Works now, fails when AWS retires the image; wrong in other regions | `data "aws_ami"` with `most_recent = true` |
| AMI lookup without `owners` | Could match a stranger's public image | Always set `owners = ["amazon"]` for AL2023 |
| Trying to `resource` something that already exists | API rejects it as a duplicate | Use a `data` source to read it, or `terraform import` to adopt it |
| Editing a managed object in the console | Next `plan` shows drift and proposes reverting your edit | Change the `.tf` file instead |
| Two resources of the same type sharing a name | Configuration will not parse | Names are unique per type per module |
| `0.0.0.0/0` inbound on SSH in a real account | The entire internet may attempt to log in | Restrict to your own address, `YOUR_IP/32` |

## Command reference

```bash
cd terraform/labs/lab03-first-ec2
terraform init
terraform plan
terraform apply
terraform state list                     # every address Terraform manages here
terraform state show aws_instance.web     # all recorded attributes of one resource
terraform output ami_id                   # which image this apply resolved to
terraform destroy                         # always, when the lab is done
```

## Where next

- The commands themselves, in order, and what each one guarantees:
  [`04-workflow.md`](04-workflow.md)
- The AWS objects lab02 built, defined properly:
  [`../../html/aws-primer.html`](../../html/aws-primer.html)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 02: Building a Network by Hand in the Console](../../labmanuals/lab02-console-vpc.md) | Click through a VPC, subnet, gateway, route table, and security group — and delete them by hand |
| [Lab 03: First EC2 Instance](../../labmanuals/lab03-first-ec2.md) | AMI data source, instance resource, tags, outputs |
