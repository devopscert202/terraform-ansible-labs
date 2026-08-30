variable "aws_region" {
  type        = string
  description = "AWS region that receives every resource in this lab."
  default     = "us-east-2"
}

variable "project" {
  type        = string
  description = "Name prefix applied to the Name tag of every resource."
  default     = "tflabs"
}

variable "vpc_cidr" {
  type        = string
  description = "IPv4 CIDR block for the VPC."
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type        = string
  description = "IPv4 CIDR block for the public subnet. Must sit inside vpc_cidr."
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web server."
  default     = "t3.micro"
}

variable "http_port" {
  type        = number
  description = "TCP port the security group opens for web traffic. Only HTTP is needed; the instance has no key pair and is never reached over SSH."
  default     = 80
}

variable "allowed_cidr" {
  type        = string
  description = "Source CIDR permitted on the ingress ports. Narrow this to your own IP/32 outside a lab account."
  default     = "0.0.0.0/0"
}
