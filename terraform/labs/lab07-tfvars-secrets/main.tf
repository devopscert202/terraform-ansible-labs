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
  settings = {
    project     = var.project
    environment = var.environment
    cost_code   = var.cost_code
  }

  name = "${var.project}-${var.environment}"

  # Every value here came out of terraform.tfvars. After apply you can read them
  # back off the VPC in the AWS console, which is the proof the file reached AWS.
  common_tags = {
    Lab         = "lab07"
    Name        = local.name
    Project     = var.project
    Environment = var.environment
    CostCode    = var.cost_code
  }
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
# db_password is deliberately absent from every tag below. A tag is readable by
# anyone with describe permission on the account, so a secret in a tag is public.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true

  tags = local.common_tags
}

resource "aws_subnet" "main" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.subnet_az

  tags = merge(local.common_tags, { Name = "${local.name}-subnet" })
}
