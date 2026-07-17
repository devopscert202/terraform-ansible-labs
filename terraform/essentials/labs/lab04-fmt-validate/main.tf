terraform {
required_version = ">= 1.5.0"
  required_providers {
    random = {
  source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

resource "random_string" "formatted_example" {
length  = 10
  special = true
  numeric = true
  upper   = true
}

output "formatted_example" {
  value     = random_string.formatted_example.result
  sensitive = true
}
