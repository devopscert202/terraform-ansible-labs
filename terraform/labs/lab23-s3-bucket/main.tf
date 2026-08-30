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
  region = var.aws_region
}

locals {
  bucket_name = "${var.bucket_prefix}-${random_pet.suffix.id}"

  common_tags = {
    Lab       = "lab23"
    ManagedBy = "Terraform"
  }
}

# S3 bucket names are globally unique across every AWS account, so any literal
# name in a shared manual is already taken. Two random dictionary words appended
# to the prefix make the name unique without the learner editing the file.
resource "random_pet" "suffix" {
  length    = 2
  separator = "-"
}

resource "aws_s3_bucket" "lab" {
  bucket = local.bucket_name

  # Allows Terraform to delete the bucket while it still holds objects. Safe in a
  # throwaway lab, destructive in production - see the manual.
  force_destroy = var.force_destroy

  tags = merge(local.common_tags, { Name = local.bucket_name })
}

# AWS provider 5.x moved every bucket setting below out of aws_s3_bucket and into
# its own resource. Older tutorials show them as inline blocks; those are gone.
resource "aws_s3_bucket_versioning" "lab" {
  bucket = aws_s3_bucket.lab.id

  versioning_configuration {
    status = var.versioning_status
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket = aws_s3_bucket.lab.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "lab" {
  bucket = aws_s3_bucket.lab.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# One object, so the bucket is not empty when force_destroy is tested.
resource "aws_s3_object" "hello" {
  bucket       = aws_s3_bucket.lab.id
  key          = var.object_key
  content      = "Managed by Terraform, lab23.\n"
  content_type = "text/plain"

  tags = merge(local.common_tags, { Name = var.object_key })
}
