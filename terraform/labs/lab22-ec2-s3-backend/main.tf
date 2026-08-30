terraform {
  # Higher than the track's >= 1.5.0 floor, for the same reason as labs 17 to 19:
  # backend.hcl.example sets use_lockfile, experimental in 1.10 and generally
  # available from 1.11. A learner on 1.5 to 1.9 would pass this check and then
  # fail at init with "Unsupported argument: use_lockfile".
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Partial configuration: bucket, key, region and locking come from backend.hcl
  # at init time, because backend blocks cannot reference variables.
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

locals {
  name = "${var.project}-remote"

  common_tags = {
    Lab     = "lab22"
    Project = var.project
  }
}

# Availability zones are per-account mappings, so "us-east-2a" is not the same
# hardware in two accounts and may not exist or have capacity in yours. Ask the
# account which zones it can actually use, then take the first.
data "aws_availability_zones" "available" {
  state = "available"
}

# Amazon Linux 2023 resolved at plan time, never a hardcoded AMI ID.
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.12-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = local.name })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${local.name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, { Name = "${local.name}-public" })
}

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

resource "aws_security_group" "web" {
  name        = "${local.name}-web"
  description = "Allow inbound HTTP, all outbound"
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

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>${local.name} is live, state in S3</h1>" > /var/www/html/index.html
  EOT

  tags = merge(local.common_tags, { Name = "${local.name}-web" })

  depends_on = [aws_route_table_association.public]
}
