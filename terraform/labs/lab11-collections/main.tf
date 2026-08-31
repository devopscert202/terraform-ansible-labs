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
  # toset() discards the duplicate the list keeps; sort() gives a stable order,
  # because a set has no order of its own.
  unique_tag_names = sort(tolist(toset(var.tag_names)))

  # A for expression over a list produces a list, still addressed by position.
  tag_labels = [for name in var.tag_names : upper(name)]

  # A for expression over a map produces a map. name is the key, subnet is the
  # object stored under it, so subnet.cidr reaches a single attribute.
  subnet_cidrs = { for name, subnet in var.subnets : name => subnet.cidr }

  # An if clause at the end of a for expression filters the result.
  zone_a_subnets = [for name, subnet in var.subnets : name if subnet.az == "us-east-2a"]

  # The three collection types side by side, counted the same way.
  collection_shapes = {
    list_length   = length(var.tag_names)
    set_length    = length(var.availability_zones)
    map_length    = length(var.subnets)
    map_keys      = keys(var.subnets)
    list_index_1  = var.tag_names[1]
    map_key_app_a = var.subnets["app_a"].cidr
  }

  common_tags = {
    Lab  = "lab11"
    Name = "lab11-collections"
  }
}

resource "terraform_data" "collections" {
  input = local.collection_shapes
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true

  tags = local.common_tags
}

# A real subnet whose two required arguments are read out of the map by key.
# var.subnets["app_a"] selects one object; .cidr and .az reach its attributes.
# This is map indexing doing real work: change the map entry and AWS changes.
#
# One resource block is still one subnet. Creating one subnet per map entry
# needs the for_each meta-argument, which Lab 24 introduces.
resource "aws_subnet" "app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnets["app_a"].cidr
  availability_zone = var.subnets["app_a"].az

  tags = merge(local.common_tags, { Name = "lab11-app-a" })
}
