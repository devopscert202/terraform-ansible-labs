variable "aws_region" {
  type        = string
  description = "AWS region the security group is created in."
  default     = "us-east-2"
}

variable "ingress_rules" {
  type = map(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
  description = "One entry per inbound rule. dynamic turns each entry into an ingress block. No SSH rule: nothing in this lab connects to a host."
  default = {
    http = {
      port        = 80
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal HTTP"
    }
    https = {
      port        = 443
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal HTTPS"
    }
  }
}
