variable "aws_region" {
  type        = string
  description = "Region for the VPC and subnet. us-east-2 has zones a, b and c only."
  default     = "us-east-2"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR of the lab VPC. Every entry in var.subnets must fit inside it."
  default     = "10.0.0.0/16"
}

variable "tag_names" {
  type        = list(string)
  description = "A list: ordered, duplicates allowed, indexed by number."
  default     = ["web", "api", "web"]
}

variable "availability_zones" {
  type        = set(string)
  description = "A set: unordered, duplicates removed automatically."
  default     = ["us-east-2a", "us-east-2b", "us-east-2a"]
}

variable "subnets" {
  type        = map(object({ cidr = string, az = string }))
  description = "A map: each value is looked up by a string key instead of a number."
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-2a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-2b" }
  }
}
