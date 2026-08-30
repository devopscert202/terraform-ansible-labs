terraform {
  required_version = ">= 1.5.0"
}

# terraform_data is a built-in placeholder resource. It creates nothing in any
# cloud, so this lab is free to run and needs no credentials.

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
}

# One resource block, one instance. Turning a collection into many copies of a
# resource needs the count and for_each meta-arguments, which Lab 24 introduces.
resource "terraform_data" "collections" {
  input = local.collection_shapes
}
