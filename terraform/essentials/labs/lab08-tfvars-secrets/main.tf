terraform {
  required_version = ">= 1.5.0"
}

locals {
  configuration = {
    cloud        = var.cloud
    department   = var.department
    cost_code    = var.cost_code
    ip_address   = var.ip_address
    phone_number = var.phone_number
  }
}

output "configuration" {
  value = {
    cloud      = local.configuration.cloud
    department = local.configuration.department
    cost_code  = local.configuration.cost_code
    ip_address = local.configuration.ip_address
  }
}

output "phone_number" {
  description = "Sensitive values are redacted in normal CLI output but remain in state."
  value       = local.configuration.phone_number
  sensitive   = true
}
