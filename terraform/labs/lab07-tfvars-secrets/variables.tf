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

# The four variables above are mandatory, which is the point of the lab. The
# three below describe the AWS network and all carry defaults, so nothing else
# has to be added to terraform.tfvars.

variable "aws_region" {
  type        = string
  description = "Region for the VPC and subnet."
  default     = "us-east-2"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR of the lab VPC."
  default     = "10.7.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR of the lab subnet. Must fit inside vpc_cidr."
  default     = "10.7.1.0/24"
}

variable "subnet_az" {
  type        = string
  description = "Zone for the subnet. us-east-2 has only zones a, b and c."
  default     = "us-east-2a"
}
