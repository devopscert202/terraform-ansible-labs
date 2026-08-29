terraform {
  required_version = ">= 1.5.0"
}

# This lab creates no cloud resources. It only shows how values arrive.
locals {
  settings = {
    project     = var.project
    environment = var.environment
    cost_code   = var.cost_code
  }
}
