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

variable "aws_region" {
  type        = string
  description = "Region for the per-workspace VPC."
  default     = "us-east-2"
}

# One CIDR per workspace, so the two VPCs can coexist without overlapping.
# terraform.workspace is a built-in value: no variable declares it, and it holds
# whichever workspace is active at the moment the command runs.
variable "workspace_cidrs" {
  type        = map(string)
  description = "CIDR per workspace name. lookup() falls back for any other name."
  default = {
    default = "10.16.0.0/16"
    dev     = "10.17.0.0/16"
  }
}

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }

  name     = "lab16-${terraform.workspace}"
  vpc_cidr = lookup(var.workspace_cidrs, terraform.workspace, "10.18.0.0/16")
}

resource "terraform_data" "workspace" { input = local.labels }

# A real VPC per workspace. Two workspaces, two states, two VPCs in the account
# at the same time — which is the proof that workspace state really is separate.
resource "aws_vpc" "env" {
  cidr_block         = local.vpc_cidr
  enable_dns_support = true

  tags = {
    Lab         = "lab16"
    Name        = local.name
    Environment = terraform.workspace
  }
}

output "workspace" { value = terraform.workspace }
output "labels" { value = terraform_data.workspace.output }

output "vpc_id" {
  description = "The VPC belonging to this workspace only. The other workspace has its own."
  value       = aws_vpc.env.id
}

output "vpc_cidr" {
  description = "CIDR selected for this workspace from var.workspace_cidrs."
  value       = aws_vpc.env.cidr_block
}

output "vpc_name" {
  description = "Name tag, built from terraform.workspace."
  value       = aws_vpc.env.tags["Name"]
}
