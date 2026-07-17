terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.aws_region }

variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "ingress_rules" {
  type = map(object({ port = number, cidr_blocks = list(string), description = string }))
  default = {
    https = { port = 443, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTPS" }
    http  = { port = 80, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTP" }
  }
}

resource "aws_security_group" "service" {
  name_prefix = "extended-dynamic-"
  description = "Dynamic ingress demonstration"
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
output "security_group_id" { value = aws_security_group.service.id }
