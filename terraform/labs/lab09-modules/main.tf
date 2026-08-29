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

# The root module calls the child module. Values go in as arguments,
# results come back out through the child module's outputs.
module "network" {
  source = "./modules/network"

  name        = var.name
  vpc_cidr    = var.vpc_cidr
  subnet_cidr = var.subnet_cidr

  tags = {
    Lab = "lab09"
  }
}
