variable "aws_region" {
  description = "AWS region every resource in this lab is created in."
  type        = string
  default     = "us-east-2"
}

variable "vpc_cidr" {
  description = "Address range of the VPC. Also the only range allowed to reach port 22."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Address range of the subnet the instance launches into. Must sit inside vpc_cidr."
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Address range of the second subnet. Must sit inside vpc_cidr and not overlap the first."
  type        = string
  default     = "10.0.2.0/24"
}

variable "public_subnet_az" {
  description = "Availability zone of the public subnet. Must exist in aws_region."
  type        = string
  default     = "us-east-2a"
}

variable "private_subnet_az" {
  description = "Availability zone of the private subnet. Must exist in aws_region."
  type        = string
  default     = "us-east-2b"
}

variable "instance_type" {
  description = "EC2 instance size."
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Name tag of the instance and the prefix for every other resource name."
  type        = string
  default     = "tf-lab03-web"
}
