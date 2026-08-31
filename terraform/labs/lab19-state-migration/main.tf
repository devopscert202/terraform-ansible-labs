terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"

  # Step 6 of the lab manual has you add the S3 backend block here:
  #   backend "s3" {}

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

resource "terraform_data" "migrated_state" { input = "migrate with terraform init -migrate-state" }

# A real VPC, which is the point of the lab. Migration moves the state file and
# must not touch this: the same vpc- id has to appear in state before and after,
# and the post-migration plan has to report no changes. With nothing real in
# state there would be nothing to prove.
resource "aws_vpc" "migrated" {
  cidr_block         = "10.19.0.0/16"
  enable_dns_support = true

  tags = {
    Lab  = "lab19"
    Name = "lab19-migrated"
  }
}

output "migration_instruction" { value = terraform_data.migrated_state.output }

output "vpc_id" {
  description = "Record this before migrating. It must be identical afterwards."
  value       = aws_vpc.migrated.id
}
