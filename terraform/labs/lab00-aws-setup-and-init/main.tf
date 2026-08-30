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
  region = "us-east-2"
}

# Reads the identity of the credentials in use. This is a data source, not a
# resource: it only reads, so nothing is created and nothing is billed.
data "aws_caller_identity" "current" {}

output "account_id" {
  description = "The AWS account number your credentials belong to."
  value       = data.aws_caller_identity.current.account_id
}

output "caller_arn" {
  description = "The full identity of the user or role Terraform is acting as."
  value       = data.aws_caller_identity.current.arn
}
