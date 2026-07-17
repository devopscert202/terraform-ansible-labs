variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "server_name" {
  type        = string
  description = "Name for the web server."
  default     = "variables-lab-web"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "tags" {
  type = map(string)
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
