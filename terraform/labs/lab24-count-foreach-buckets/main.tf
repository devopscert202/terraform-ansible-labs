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

# S3 bucket names are unique across every AWS account on earth, not just yours.
# A random suffix keeps this lab runnable by everyone at once without editing
# any name by hand.
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  prefix = "${var.name_prefix}-${random_id.suffix.hex}"

  common_tags = {
    Lab = "lab24"
  }
}

# count: N interchangeable copies, addressed by POSITION.
# Every instance below is configured identically. Only the name changes, and it
# changes because the position in the list changes - not because the bucket has
# an identity of its own.
resource "aws_s3_bucket" "by_count" {
  count = length(var.bucket_names)

  bucket        = "${local.prefix}-count-${var.bucket_names[count.index]}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name  = "${local.prefix}-count-${var.bucket_names[count.index]}"
    Index = tostring(count.index)
  })
}

# for_each: N differently-configured instances, addressed by NAME.
# each.key is the map key, each.value is the object stored under it, so every
# instance can carry its own settings.
resource "aws_s3_bucket" "by_each" {
  for_each = var.buckets

  bucket        = "${local.prefix}-${each.key}"
  force_destroy = true

  tags = merge(each.value.tags, local.common_tags, {
    Name = "${local.prefix}-${each.key}"
  })
}

# AWS provider 5.x moved versioning out of aws_s3_bucket into its own resource.
# It iterates the same map, and reaches its own bucket by key:
# aws_s3_bucket.by_each[each.key].id
resource "aws_s3_bucket_versioning" "by_each" {
  for_each = var.buckets

  bucket = aws_s3_bucket.by_each[each.key].id

  versioning_configuration {
    status = each.value.versioning ? "Enabled" : "Suspended"
  }
}
