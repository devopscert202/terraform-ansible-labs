terraform {
  required_version = ">= 1.5.0"
}

variable "availability_zones" {
  type    = set(string)
  default = ["us-east-1a", "us-east-1b"]
}
variable "subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}

resource "terraform_data" "subnet" {
  for_each = var.subnets
  input    = { name = each.key, cidr = each.value.cidr, az = each.value.az }
}

output "zones" { value = sort(tolist(var.availability_zones)) }
output "subnet_ids" { value = { for name, item in terraform_data.subnet : name => item.id } }
