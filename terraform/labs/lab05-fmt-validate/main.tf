terraform {
  required_version = ">= 1.5.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  course = "terraform-labs"
}

# terraform_data stores a value in state without calling any API, which gives
# the state commands something real to inspect at zero cost.
resource "terraform_data" "validation_probe" {
  input = local.course
}

resource "random_string" "formatted_example" {
  length  = 10
  special = true
  numeric = true
  upper   = true
}

output "validation_probe" {
  description = "Value the probe resource recorded in state."
  value       = terraform_data.validation_probe.output
}

output "formatted_example" {
  description = "Random string, hidden from normal CLI display."
  value       = random_string.formatted_example.result
  sensitive   = true
}
