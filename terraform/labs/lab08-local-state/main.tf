terraform {
  required_version = ">= 1.5.0"
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

# There is no backend block, so Terraform writes state to ./terraform.tfstate.

provider "aws" {
  region = "us-east-2"
}

resource "random_pet" "server" {
  prefix = "lab08"
  length = 2
}

# A generated secret. It is stored in terraform.tfstate as plain text.
resource "random_password" "db" {
  length  = 16
  special = false
}

# A real VPC, so state holds an ID that AWS also holds. This is what makes the
# state file worth protecting: lose it and the VPC still exists, but Terraform
# no longer knows about it and the next apply creates a second one.
resource "aws_vpc" "main" {
  cidr_block         = "10.8.0.0/16"
  enable_dns_support = true

  tags = {
    Lab  = "lab08"
    Name = random_pet.server.id
  }
}
