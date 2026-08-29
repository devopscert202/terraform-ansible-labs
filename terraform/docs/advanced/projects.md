# Project Layout, Multiple Providers, and the Capstone

Deep dive for lab13 and lab21. Covers how to organise a repository once one directory is no longer
enough, how several providers coexist in one configuration, how environments get promoted, and how
lab21's capstone fits together resource by resource.

## From one directory to a repository

Every lab so far has been one root module in one directory. Real projects outgrow that, and the
question becomes where to draw the boundaries.

The unit that matters is the **state file**, because state is the unit of locking, of applying, and
of blast radius. Everything in one state is planned together, applied together, and can be
destroyed together. So "how should I split my repository" is really "what should share a state
file".

Three shapes, in increasing order of separation:

| Shape | Layout | Splits state by |
|---|---|---|
| Single root | One directory, all resources | Nothing. One state for everything |
| Root per environment | `environments/dev/`, `environments/prod/`, calling shared `modules/` | Environment |
| Root per environment per component | `environments/prod/network/`, `environments/prod/app/` | Environment and component |

```
terraform/
├── modules/                 <- reusable, no backend, no provider block
│   ├── network/
│   └── app/
└── environments/
    ├── dev/
    │   ├── network/         <- root module: backend + provider + module calls
    │   │   ├── main.tf
    │   │   └── backend.hcl
    │   └── app/
    └── prod/
        ├── network/
        └── app/
```

Two rules make this work, and both come from earlier labs. Modules never declare a `backend` or a
`provider` — those belong to the root, so the same module can serve dev and prod (lab09). And each
root gets its own state key, so each has its own lock and its own blast radius (lab18).

The trade-off is real: more roots means more applies to run and more coordination between them,
usually via `terraform_remote_state` (lab20). Start with fewer roots and split when a specific pain
appears — a slow plan, a lock you keep waiting on, a change that keeps touching things it should
not.

**Visual summary:** [`../../html/advanced.html`](../../html/advanced.html)

## Multiple providers in one configuration (lab13)

A configuration can register as many providers as it needs. Lab13 uses two:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }
provider "random" {}

resource "random_pet" "label" { length = 2 }

output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}
```

Terraform routes each resource to a provider by the prefix of its type: `aws_*` goes to the `aws`
provider, `random_*` to `random`. There is no configuration needed to connect them, and no ordering
problem — the dependency graph spans providers freely, so an `aws_instance` can take its name from a
`random_pet` and Terraform will resolve the order.

`provider "random" {}` is empty because the random provider has nothing to configure. It could be
omitted entirely; declaring it in `required_providers` is sufficient.

### Aliases for the same provider twice

The more common real case is one provider configured two ways — usually two regions:

```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-west-2"
}

resource "aws_s3_bucket" "primary" {
  bucket = "${var.project}-primary"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.dr
  bucket   = "${var.project}-replica"
}
```

Resources with no `provider` argument use the unaliased default. To pass an aliased provider into a
child module, use `providers` (plural) on the `module` block:

```hcl
module "dr_network" {
  source = "./modules/network"

  providers = {
    aws = aws.dr
  }
}
```

Note the asymmetry: `provider` (singular) on a resource, `providers` (plural, a map) on a module.

## The capstone (lab21)

Lab21 is the payoff for the whole track: a working public web server built from nothing. It uses
almost every concept in this repository at once. Worth reading as seven resources, in dependency
order — the same order lab02 made you click through by hand.

### 1. The AMI lookup

```hcl
# Amazon Linux 2023 resolved at plan time, never a hardcoded AMI ID.
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}
```

Same pattern as lab03: newest Amazon Linux 2023, published by Amazon, never a literal `ami-...`.

### 2. The VPC

```hcl
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = local.name })
}
```

`10.0.0.0/16` is your private address range — 65,536 addresses nobody else can see.
`enable_dns_hostnames` matters more than it looks: without it, instances get no public DNS name.

### 3. The internet gateway

```hcl
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${local.name}-igw" })
}
```

The door between the VPC and the internet. Attaching it grants no connectivity by itself — a route
must point at it, which is step 5.

### 4. The public subnet

```hcl
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, { Name = "${local.name}-public" })
}
```

`10.0.1.0/24` is a slice of the VPC range, pinned to one availability zone.
`map_public_ip_on_launch = true` is what makes it "public" in practice — instances launched here get
a public IP automatically.

### 5. The route table

```hcl
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.common_tags, { Name = "${local.name}-public-rt" })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

`0.0.0.0/0` means "everywhere not already covered by a more specific route", so this is the default
route: anything not local goes out through the gateway. The association is a separate resource
because a route table is not attached to anything until you say which subnets use it — a
frequently-forgotten step, and one of the more confusing failures when omitted, since everything
appears to be built correctly and nothing can reach the internet.

### 6. The security group

```hcl
resource "aws_security_group" "web" {
  name        = "${local.name}-web"
  description = "Allow inbound web and SSH, all outbound"
  vpc_id      = aws_vpc.this.id

  dynamic "ingress" {
    for_each = var.ingress_ports
    content {
      description = "Inbound TCP ${ingress.value}"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    }
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.name}-web-sg" })
}
```

This is lab12's `dynamic` block doing real work: `var.ingress_ports` defaults to `[80, 22]` and
generates one `ingress` block per port. Adding a port is a variable change, not a structural one.

Security groups are stateful — the `egress` rule permits outbound traffic, and replies to it return
automatically without a matching ingress rule. `allowed_cidr` defaults to `0.0.0.0/0` so the lab
works from any network; narrow it to `YOUR_IP/32` in any account you care about.

### 7. The instance

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>${local.name} is live</h1>" > /var/www/html/index.html
  EOT

  tags = merge(local.common_tags, { Name = "${local.name}-web" })

  depends_on = [aws_route_table_association.public]
}
```

Two details carry the lesson of the whole advanced tier.

**`user_data` instead of a provisioner.** The `<<-EOT` heredoc is a shell script cloud-init runs at
first boot. No SSH, no `connection` block, no network path from Terraform to the instance, nothing
to hang. Compare with lab15's `remote-exec` and the difference in fragility is the argument
[`provisioners.md`](provisioners.md) makes.

**`depends_on` on the route table association.** The instance reads no attribute from the
association, so Terraform sees no dependency — but the `dnf install` in `user_data` needs working
internet routing. Without this line, the instance sometimes boots before the route exists and the
package install fails silently. This is the textbook case for an explicit `depends_on`: a real
dependency that no reference expresses.

### The outputs

```hcl
output "web_url" {
  description = "Full URL of the web server. Open it or curl it to verify the build."
  value       = "http://${aws_instance.web.public_ip}"
}
```

The verification step is the point. `curl` that URL, get the HTML back, and every one of the seven
resources is proven working end to end.

Give `user_data` a minute or two after apply completes. Terraform reports success when AWS says the
instance is running, which is before cloud-init has finished installing httpd — so a connection
refused immediately after apply usually means "wait a moment", not "broken".

## Environment promotion

The same code should reach production, having been proven everywhere else first. What changes
between environments is inputs, not code.

| Stage | State | Approval | Applied by |
|---|---|---|---|
| **Dev** | `labs/dev/...` | None. Destroy and rebuild freely | Anyone on the team |
| **Staging** | `labs/staging/...` | Plan reviewed on the pull request | CI, on merge |
| **Prod** | `labs/prod/...` | Plan reviewed and explicitly approved | CI only, never a laptop |

Three practices make this work in practice:

- **Pin module and provider versions in prod.** Unpinned means someone else's commit changes your
  production infrastructure with no action from you.
- **Apply the saved plan.** `terraform plan -out=tfplan` in one stage, `terraform apply tfplan` in
  the next, so the diff that gets approved is the diff that runs. Treat the plan file as secret; it
  contains the full diff, secrets included.
- **Detect drift on a schedule.** A nightly `terraform plan` that reports non-empty output tells you
  someone changed production by hand, near when it happened rather than months later.

## Project hygiene checklist

- [ ] Remote backend with `encrypt = true` and `use_lockfile = true`
- [ ] S3 bucket versioning enabled, with a lifecycle policy on old versions
- [ ] State key includes both environment and component
- [ ] No credentials in version control — environment variables locally, OIDC in CI
- [ ] `terraform.tfvars.example` documents every variable, with placeholders
- [ ] `.gitignore` covers `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `backend.hcl`, real `*.tfvars`
- [ ] `.terraform.lock.hcl` **is** committed
- [ ] Provider and module versions pinned
- [ ] `terraform fmt -check -recursive` and `terraform validate` run in CI
- [ ] README states how to `init` with the right backend config
- [ ] Every AWS resource tagged for ownership and cost
- [ ] Teardown documented, and actually run on lab and sandbox accounts

## Command reference

```bash
cd terraform/labs/lab13-multi-provider
terraform init
terraform plan
terraform apply
terraform providers        # confirm both providers resolved
terraform destroy

cd ../lab21-capstone-vpc-ec2
cp terraform.tfvars.example terraform.tfvars     # narrow allowed_cidr to your IP
terraform init
terraform plan -out=tfplan                        # expect 7 resources to add
terraform apply tfplan
curl "$(terraform output -raw web_url)"           # the payoff
terraform destroy                                 # an EC2 instance bills by the hour
```

`terraform output -raw web_url` is the correct use of `-raw`: it strips the quotes so the value can
be handed straight to `curl`.

## Where next

- Where state for these layouts lives: [`state.md`](state.md)
- Why lab21 uses `user_data` and not `remote-exec`: [`provisioners.md`](provisioners.md)
- The AWS objects lab21 builds, defined from scratch:
  [`../../html/aws-primer.html`](../../html/aws-primer.html)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 13: Multi-Provider](../../labmanuals/lab13-multi-provider.md) | Two providers in one root module, and provider aliases |
| [Lab 21: Capstone — VPC and EC2](../../labmanuals/lab21-capstone-vpc-ec2.md) | VPC, subnet, gateway, route table, security group, and a live web server |
