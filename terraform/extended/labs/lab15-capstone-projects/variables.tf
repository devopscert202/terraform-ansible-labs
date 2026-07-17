variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "project" {
  type    = string
  default = "capstone"
}
variable "vpc_cidr" {
  type    = string
  default = "10.50.0.0/16"
}
variable "public_subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    public_a = { cidr = "10.50.1.0/24", az = "us-east-1a" }
    public_b = { cidr = "10.50.2.0/24", az = "us-east-1b" }
  }
}
variable "tags" {
  type    = map(string)
  default = { managed_by = "terraform", course = "extended" }
}
