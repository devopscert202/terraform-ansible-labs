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

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.1-x86_64"]
  }
}

# Locals are values computed inside the configuration. Nobody outside can set them.
locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
    Lab  = "lab06"
  })

  # coalesce() returns the first non-null, non-empty argument, so a null variable
  # falls through to the fallback.
  contact = coalesce(var.owner_email, "unset@example.invalid")

  # null and "" are different values, and only an equality test tells them apart.
  owner_email_state = (
    var.owner_email == null ? "null: no value was supplied" :
    var.owner_email == "" ? "empty string: a value was supplied and it is blank" :
    "set: ${var.owner_email}"
  )

  # Numbers support arithmetic; the same digits held as a string would not.
  total_disk_gb = var.root_volume_gb + sum([for d in var.disks : d.size_gb])

  # Same default value in both variables, different element count.
  list_vs_set = {
    list_length = length(var.role_list)
    set_length  = length(var.role_set)
    first_item  = var.role_list[0]
  }
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true
  tags               = local.common_tags
}

resource "aws_subnet" "main" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.subnet_az
  tags              = local.common_tags
}

# Port 22 is reachable only from inside the VPC. There is no internet gateway and
# no public IP, so nothing outside this VPC can connect at all.
resource "aws_security_group" "instance" {
  name        = "${var.server_name}-sg"
  description = "Lab 06 instance security group"
  vpc_id      = aws_vpc.main.id
  tags        = local.common_tags

  ingress {
    description = "SSH from inside the VPC only"
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
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  monitoring             = var.enable_detailed_monitoring
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.instance.id]
  tags                   = local.common_tags

  root_block_device {
    volume_size = var.root_volume_gb
    tags        = local.common_tags
  }
}
