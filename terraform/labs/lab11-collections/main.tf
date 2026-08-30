terraform {
  required_version = ">= 1.5.0"
}

# terraform_data is a built-in placeholder resource. It creates nothing in any
# cloud, so this lab is free to run and needs no credentials.

# count makes copies addressed by number: terraform_data.by_count[0], [1], [2].
resource "terraform_data" "by_count" {
  count = length(var.tag_names)
  input = var.tag_names[count.index]
}

# for_each makes copies addressed by key: terraform_data.by_each["app_a"].
resource "terraform_data" "by_each" {
  for_each = var.subnets
  input = {
    name = each.key
    cidr = each.value.cidr
    az   = each.value.az
  }
}
