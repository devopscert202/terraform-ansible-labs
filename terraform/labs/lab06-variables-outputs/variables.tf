variable "aws_region" {
  type        = string
  description = "AWS region the instance is created in."
  default     = "us-east-1"
}

variable "server_name" {
  type        = string
  description = "Value used for the Name tag on the EC2 instance."
  default     = "lab06-web"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size."
  default     = "t3.micro"
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
