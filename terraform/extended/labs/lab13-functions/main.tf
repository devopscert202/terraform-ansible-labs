terraform {
  required_version = ">= 1.5.0"
}

variable "application" {
  type    = string
  default = "payments api"
}
variable "cidrs" {
  type    = list(string)
  default = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}

locals {
  slug          = lower(replace(var.application, " ", "-"))
  unique_cidrs  = sort(tolist(toset(var.cidrs)))
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)
  configuration = jsonencode({ name = local.slug, cidrs = local.unique_cidrs })
}
resource "terraform_data" "functions" { input = local.configuration }
output "results" { value = { slug = local.slug, cidrs = local.unique_cidrs, subnet = local.subnet_prefix, json = terraform_data.functions.output } }
