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

# Looks up the newest Amazon Linux 2023 image at plan time. Hardcoding an AMI id
# would break as soon as AWS publishes a replacement.
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.12-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# The network this lab builds for itself. Without it the instance below would
# have no subnet_id and would silently require the region's default VPC.
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name      = "${var.instance_name}-vpc"
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
}

# Named "public" for the role it will play in Lab 10. With no internet gateway
# and no route table it is still a private subnet today.
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.public_subnet_az

  tags = {
    Name      = "${var.instance_name}-public"
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = var.private_subnet_az

  tags = {
    Name      = "${var.instance_name}-private"
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
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

  tags = {
    Name      = "${var.instance_name}-sg"
    Lab       = "lab03"
    ManagedBy = "Terraform"
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
