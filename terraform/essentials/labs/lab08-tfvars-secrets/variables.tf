variable "cloud" {
  type        = string
  description = "Cloud provider name in lowercase."

  validation {
    condition     = contains(["aws", "azure", "gcp", "vmware"], var.cloud)
    error_message = "cloud must be aws, azure, gcp, or vmware in lowercase."
  }
}

variable "department" {
  type = string

  validation {
    condition     = lower(var.department) == var.department
    error_message = "department must be lowercase."
  }
}

variable "cost_code" {
  type = string

  validation {
    condition     = length(var.cost_code) == 3
    error_message = "cost_code must contain exactly three characters."
  }
}

variable "ip_address" {
  type = string

  validation {
    condition     = can(cidrhost("${var.ip_address}/32", 0))
    error_message = "ip_address must be a valid IPv4 address."
  }
}

variable "phone_number" {
  type        = string
  description = "Example secret; pass through TF_VAR_phone_number or an ignored tfvars file."
  sensitive   = true
}
