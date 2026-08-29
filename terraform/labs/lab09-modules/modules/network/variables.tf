# These are the module's inputs. The caller must supply name, vpc_cidr and subnet_cidr.
variable "name" {
  type        = string
  description = "Name prefix applied to every resource in this module."
}

variable "vpc_cidr" {
  type        = string
  description = "IP address range for the VPC."
}

variable "subnet_cidr" {
  type        = string
  description = "IP address range for the subnet."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into every resource in this module."
  default     = {}
}
