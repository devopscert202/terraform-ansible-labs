terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}

output "generated_value" {
  value = random_string.example.result
}
