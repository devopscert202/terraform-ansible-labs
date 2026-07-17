variable "aws_region" {
  description = "AWS region for the instance."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance."
  type        = string
  default     = "terraform-essentials-web"
}

variable "ssh_cidr" {
  description = "CIDR allowed to SSH to the instance (use your public IP/32)."
  type        = string
}
