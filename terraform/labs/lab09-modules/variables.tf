variable "aws_region" {
  type        = string
  description = "AWS region the network is created in."
  default     = "us-east-1"
}

variable "name" {
  type        = string
  description = "Name prefix applied to the VPC and subnet."
  default     = "lab09"
}

variable "vpc_cidr" {
  type        = string
  description = "IP address range for the VPC."
  default     = "10.42.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "IP address range for the subnet. Must sit inside vpc_cidr."
  default     = "10.42.1.0/24"
}
