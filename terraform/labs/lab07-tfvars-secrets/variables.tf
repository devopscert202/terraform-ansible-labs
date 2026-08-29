variable "project" {
  type        = string
  description = "Project name. Set in terraform.tfvars."
}

variable "environment" {
  type        = string
  description = "Deployment environment, lowercase. Set in terraform.tfvars."

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "cost_code" {
  type        = string
  description = "Three-character billing code. Set in terraform.tfvars."

  validation {
    condition     = length(var.cost_code) == 3
    error_message = "cost_code must contain exactly three characters."
  }
}

variable "db_password" {
  type        = string
  description = "Database password. Never put this in a committed file; export TF_VAR_db_password instead."
  sensitive   = true
}
