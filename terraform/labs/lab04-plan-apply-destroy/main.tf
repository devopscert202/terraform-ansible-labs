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

provider "aws" {
  region = "us-east-2"
}

# A locally generated suffix, so the VPC gets a name you did not choose. It also
# gives the lifecycle something to show: the string is created before the VPC and
# destroyed after it, because the VPC depends on it.
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
  numeric = false
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
# A VPC is free, and creating one is the smallest real thing AWS will build for
# you, which makes it the right subject for a lab about the lifecycle itself.
resource "aws_vpc" "lifecycle" {
  cidr_block         = "10.4.0.0/16"
  enable_dns_support = true

  tags = {
    Lab  = "lab04"
    Name = "lab04-${random_string.suffix.result}"
  }
}

output "generated_value" {
  description = "The locally generated suffix, before it reaches AWS."
  value       = random_string.suffix.result
}

output "vpc_id" {
  description = "The ID AWS assigned. This value did not exist until apply ran."
  value       = aws_vpc.lifecycle.id
}

output "vpc_name" {
  description = "The Name tag AWS recorded, built from the generated suffix."
  value       = aws_vpc.lifecycle.tags["Name"]
}
