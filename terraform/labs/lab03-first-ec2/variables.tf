variable "aws_region" {
  description = "AWS region the instance is created in."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance size."
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Value of the Name tag on the instance."
  type        = string
  default     = "tf-lab03-web"
}
