terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  # String functions: force lowercase, then swap spaces for hyphens.
  slug = lower(replace(var.application, " ", "-"))

  # Collection functions: toset() drops duplicates, sort() gives a stable order.
  unique_cidrs = sort(tolist(toset(var.cidrs)))

  # Numeric and network functions. subnet_prefix is derived from the VPC's own
  # CIDR, so widening the VPC moves the subnet with it and neither is retyped.
  cidr_count    = length(local.unique_cidrs)
  subnet_prefix = cidrsubnet(var.vpc_cidr, var.subnet_newbits, var.subnet_netnum)

  # Encoding functions: build a JSON string from a Terraform object.
  config_json = jsonencode({
    name  = local.slug
    cidrs = local.unique_cidrs
  })

  # Formatting: build a display string from several values.
  summary = format("%s uses %d unique CIDR(s)", local.slug, local.cidr_count)

  common_tags = {
    Lab     = "lab12"
    Name    = local.slug
    Summary = local.summary
  }
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true

  tags = local.common_tags
}

# cidrsubnet() doing real work. The CIDR below was never typed by hand: it is
# computed from var.vpc_cidr, so this is the arithmetic the function replaced.
resource "aws_subnet" "derived" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.subnet_prefix
  availability_zone = var.subnet_az

  tags = merge(local.common_tags, { Name = "${local.slug}-derived" })
}

# The deduplicated, sorted CIDR list becomes the real source ranges of a real
# security group. There is no internet gateway, so nothing outside reaches this.
resource "aws_security_group" "app" {
  name        = "${local.slug}-sg"
  description = "Lab 12: ingress ranges built by toset(), tolist() and sort()"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from the deduplicated CIDR list"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = local.unique_cidrs
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.slug}-sg" })
}
