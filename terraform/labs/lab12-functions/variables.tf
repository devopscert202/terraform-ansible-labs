variable "aws_region" {
  type        = string
  description = "Region for the VPC, subnet and security group."
  default     = "us-east-2"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR of the lab VPC. cidrsubnet() carves the subnet range out of this."
  default     = "10.20.0.0/16"
}

variable "subnet_newbits" {
  type        = number
  description = "Bits cidrsubnet() adds to vpc_cidr. 8 added to a /16 gives /24 blocks."
  default     = 8
}

variable "subnet_netnum" {
  type        = number
  description = "Which block cidrsubnet() selects, counting from zero. 12 gives the thirteenth."
  default     = 12
}

variable "subnet_az" {
  type        = string
  description = "Zone for the derived subnet. us-east-2 has only zones a, b and c."
  default     = "us-east-2a"
}

variable "application" {
  type        = string
  description = "Human-written application name, used to build a machine-safe slug."
  default     = "Payments API"
}

variable "cidrs" {
  type        = list(string)
  description = "Raw CIDR list, deliberately unsorted and containing a duplicate."
  default     = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}
