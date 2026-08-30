# The Capstone: VPC to Public Web Server

Backs lab 10. Covers how the capstone fits together resource by resource, why each one is needed,
and the two details — `user_data` and `depends_on` — that carry the most weight.

Lab10 sits mid-track on purpose. Everything before it is a piece: a provider, a resource, a
variable, a module. This is the first lab where the pieces make something a person can open in a
browser. Read it as seven resources in dependency order — the same order lab02 made you click
through by hand.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html) · Architecture
diagram: [`../html/aws-primer.html`](../html/aws-primer.html)

## 1. The AMI lookup

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

## 2. The VPC

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

## 3. The internet gateway

```hcl
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${local.name}-igw" })
}
```

The door between the VPC and the internet. Attaching it grants no connectivity by itself — a route
must point at it, which is step 5.

## 4. The public subnet

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, { Name = "${local.name}-public" })
}
```

`10.0.1.0/24` is a slice of the VPC range, pinned to one availability zone.
`map_public_ip_on_launch = true` is what makes it "public" in practice — instances launched here get
a public IP automatically.

The zone is never hardcoded. `us-east-2` publishes three zones, `us-east-2a` through `us-east-2c`,
but zone names are mapped per account, so `us-east-2a` is not the same hardware in two accounts and
may be out of capacity in yours. `data "aws_availability_zones"` asks the account which zones it can
actually use and `names[0]` takes the first; a subnet is zonal, so it must name exactly one.

## 5. The route table

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

## 6. The security group

```hcl
resource "aws_security_group" "web" {
  name        = "${local.name}-web"
  description = "Allow inbound web traffic, all outbound"
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

`var.ingress_ports` defaults to `[80]` and the `dynamic` block generates one `ingress` block per
port, so adding a port is a variable change rather than a structural one. There is deliberately no
SSH rule: the instance has no key pair and nothing in this lab connects to it. Lab21 takes the same
technique further and is the deep dive on it — [`14-dynamic-blocks.md`](14-dynamic-blocks.md).

Security groups are stateful — the `egress` rule permits outbound traffic, and replies to it return
automatically without a matching ingress rule. `allowed_cidr` defaults to `0.0.0.0/0` so the lab
works from any network; narrow it to `YOUR_IP/32` in any account you care about.

## 7. The instance

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

Two details carry a lesson the later labs return to.

**`user_data` instead of a provisioner.** The `<<-EOT` heredoc is a shell script cloud-init runs at
first boot. No SSH, no `connection` block, no network path from Terraform to the instance, nothing
to hang. Compare with lab15's `remote-exec` and the difference in fragility is the argument
[`11-provisioners.md`](11-provisioners.md) makes.

**`depends_on` on the route table association.** The instance reads no attribute from the
association, so Terraform sees no dependency — but the `dnf install` in `user_data` needs working
internet routing. Without this line, the instance sometimes boots before the route exists and the
package install fails silently. This is the textbook case for an explicit `depends_on`: a real
dependency that no reference expresses.

## The outputs

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

## Command reference

```bash
cd terraform/labs/lab10-capstone-vpc-ec2
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

- The AWS objects this lab builds, each defined from scratch:
  [`../html/aws-primer.html`](../html/aws-primer.html)
- The same topology again with its state in S3, at lab22: [`13-remote-state.md`](13-remote-state.md)
- Why it uses `user_data` and not `remote-exec`:
  [`11-provisioners.md`](11-provisioners.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 10: Capstone — VPC to public web server](../labmanuals/lab10-capstone-vpc-ec2.md) | VPC, subnet, gateway, route table, security group, and a live web server |
