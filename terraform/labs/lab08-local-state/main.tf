terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# There is no backend block, so Terraform writes state to ./terraform.tfstate.
resource "random_pet" "server" {
  prefix = "lab08"
  length = 2
}

# A generated secret. It is stored in terraform.tfstate as plain text.
resource "random_password" "db" {
  length  = 16
  special = false
}
