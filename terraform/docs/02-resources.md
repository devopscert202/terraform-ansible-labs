# Terraform Resources and Data Sources

Backs lab 03. Covers what it means for Terraform to *own* a resource, how resources are addressed
and referenced, how Terraform works out the order to build things in, and why tags matter more than
they look.

## Ownership is the whole idea

A **resource** is an object Terraform owns. Ownership means three specific things: Terraform knows
the object's real ID, it records the object's attributes in state, and it will create, modify, or
delete the object to make reality match your configuration.

A **data source** is a read-only question. Terraform reads it and never changes it.

The shortest way to keep them straight: a resource is a **promise** Terraform makes about the
world, while a data source is a **question** it asks about the world. Anything inside a `resource`
block is something you are claiming responsibility for — including its eventual deletion.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

The contrast with building the same objects by hand in the console is lab02, written up in
[`01-providers.md`](01-providers.md).

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

Lab10 uses exactly this, because an instance's user-data script needs working internet routing to
install packages, yet the instance reads no attribute from the route table association. Use
`depends_on` sparingly; if you find yourself adding many, you are usually missing a reference.

## Lab03: your first real AWS resources

Lab03 builds a small network and puts one EC2 instance in it: a VPC, a public and a private subnet, a
security group, and the instance, plus an AMI data source.

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

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  # tags omitted
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.public_subnet_az
}

resource "aws_security_group" "instance" {
  name        = "${var.instance_name}-sg"
  description = "SSH from inside the VPC only, all outbound"
  vpc_id      = aws_vpc.main.id

  # var.vpc_cidr, not 0.0.0.0/0: only addresses inside this VPC may reach 22.
  ingress {
    description = "SSH from within the VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
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

Four details deserve attention.

**The AMI is looked up, never hardcoded.** An **AMI** (Amazon Machine Image) is the disk image the
instance boots from. Its ID differs in every region and is replaced every few weeks as Amazon
publishes patched images, so a literal `ami-0abc123...` in your configuration is a time bomb: it
works today, and fails in three months when the image is deregistered. The data source asks for
"newest Amazon Linux 2023" and gets a currently valid ID every time. `owners = ["amazon"]` is not
decoration — without it, a public image from an unrelated account with a similar name could match.

**The instance type is `t3.micro`.** That is the size — 2 vCPU, 1 GiB memory. It is the smallest
current-generation general-purpose size, and it is what every AWS lab in this track uses.

**The network is stated, not inherited.** `subnet_id` on the instance and `vpc_id` on the security
group both point at resources lab03 creates itself. That is deliberate and it is the more important
lesson of the two: an `aws_instance` with no `subnet_id`, or an `aws_security_group` with no
`vpc_id`, silently falls back to the region's **default VPC** — and `terraform plan` cannot detect
that the account has none, so the failure appears only at apply as
`VPCIdNotSpecified: No default VPC for this user`. Naming the network removes the whole class of
problem. Lab06 does the same for the same reason.

**The instance is deliberately unreachable.** There is no internet gateway, no route to `0.0.0.0/0`
and no public IP, and the security group admits port 22 only from inside the VPC's own CIDR range.
You can prove the instance exists and read its ID; you cannot connect to it. Public reachability is
lab10's payoff.

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
| `aws_instance` with no `subnet_id`, or `aws_security_group` with no `vpc_id` | Silently requires a default VPC; `plan` passes and apply fails with `VPCIdNotSpecified` | Create a VPC and subnet and name them, as lab03 does |

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
  [`03-workflow.md`](03-workflow.md)
- Every AWS object named here, defined from scratch:
  [`../html/aws-primer.html`](../html/aws-primer.html)
- The same network with an internet gateway and a reachable web server, at lab10:
  [`08-capstone.md`](08-capstone.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 03: First EC2 Instance](../labmanuals/lab03-first-ec2.md) | VPC, subnets, security group, AMI data source, instance resource, tags, outputs |
